#!/bin/bash
# Same discovery contract as the glm53 EXL3 lane: validate the node-local
# inventory against this pod's node/host, then export NCCL env selecting
# the peer-facing RoCE rails. TensorFold drives collectives through NCCL,
# and patch 0006's RoCE proxy reads TF_ROCE_HCA / TF_ROCE_GID_INDEX with
# NCCL_IB_HCA / NCCL_IB_GID_INDEX fallbacks — all covered by these exports.
# Only the recipe's measured-minimal NCCL set is exported; extra NCCL
# tuning knobs kept NCCL on one rail upstream and are deliberately omitted.
#
# Routed mode (OQ-0055): on a switchless ring, non-adjacent node pairs have
# zero direct rails. When the inventory shows no rails to the peer but the
# host has routed fabric paths (dotfiles installs static routes via the ring
# neighbour, ip_forward=1), fall back to routed RoCE v2: NCCL bootstrap moves
# to the control-plane interface, all local fabric HCAs are advertised, and
# rdma_cm resolves peer GIDs over the forwarded hop (measured 889 MB/s RDMA
# over a kernel-forwarded neighbour on an identical ring by alexellis).
set -euo pipefail
: "${PEER_SERVICE:?PEER_SERVICE is required}"
: "${HOST_IP:?HOST_IP is required}"
: "${NODE_NAME:?NODE_NAME is required}"
inventory=/etc/dgx-spark/rdma-fabric.json
test -s "$inventory"

echo "waiting for peer endpoint $PEER_SERVICE"
while true; do
  PEER_CONTROL_IP="$(getent ahostsv4 "$PEER_SERVICE" 2>/dev/null | awk -v self="$HOST_IP" '$1 != self { print $1; exit }' || true)"
  [ -n "$PEER_CONTROL_IP" ] && break
  sleep 2
done
export PEER_CONTROL_IP

eval "$(python3 - "$inventory" "$PEER_CONTROL_IP" "$NODE_NAME" "$HOST_IP" <<'PY'
import ipaddress
import json
import pathlib
import shlex
import sys

inventory_path, peer_control_ip, node_name, host_ip = sys.argv[1:]
fabric = json.loads(pathlib.Path(inventory_path).read_text())
if fabric["nodeName"] != node_name:
    raise SystemExit(
        f"fabric inventory node {fabric['nodeName']} does not match scheduled node {node_name}"
    )
if fabric["controlPlane"]["address"] != host_ip:
    raise SystemExit(
        f"fabric control address {fabric['controlPlane']['address']} does not match host IP {host_ip}"
    )

# Ring membership map for peer naming in routed mode (informational + logs).
CONTROL_NODE_BY_IP = {
    "172.16.4.54": "astrolabe",
    "172.16.4.55": "chronometer",
    "172.16.4.56": "sextant",
    "172.16.4.57": "octant",
}

links = [
    link for link in fabric["links"]
    if link["peerControlAddress"] == peer_control_ip
]
if len(links) not in (0, 2):
    raise SystemExit(
        f"expected two rails to peer {peer_control_ip}, found {len(links)}"
    )
mode = "direct" if len(links) == 2 else "routed"

if mode == "routed":
    # No direct rails: serve over routed RoCE v2 through the ring neighbour.
    # Requires dotfiles routed-fabric routes + ip_forward on the transit node.
    links = list(fabric["links"])

hcas = []
gid_indexes = set()
netdevs = []
local_addresses = []
peer_addresses = []
for link in links:
    netdev = link["interface"]
    netdevs.append(netdev)
    hca_dir = pathlib.Path("/sys/class/net") / netdev / "device/infiniband"
    hca_names = sorted(path.name for path in hca_dir.iterdir())
    if len(hca_names) != 1:
        raise SystemExit(f"expected one HCA for {netdev}, found {hca_names}")
    hca = hca_names[0]
    hcas.append(f"{hca}:1")

    local_ip = ipaddress.ip_interface(link["address"]).ip
    local_addresses.append(str(local_ip))
    peer_addresses.append(link["peerAddress"])
    gid_root = pathlib.Path("/sys/class/infiniband") / hca / "ports/1"
    matches = []
    for gid_path in sorted((gid_root / "gids").iterdir(), key=lambda p: int(p.name)):
        index = gid_path.name
        try:
            gid_type = (gid_root / "gid_attrs/types" / index).read_text().strip()
            gid_netdev = (gid_root / "gid_attrs/ndevs" / index).read_text().strip()
            gid = ipaddress.ip_address(gid_path.read_text().strip())
        except (OSError, ValueError):
            continue
        if gid_type == "RoCE v2" and gid_netdev == netdev and gid.ipv4_mapped == local_ip:
            matches.append(index)
    if len(matches) != 1:
        raise SystemExit(f"expected one RoCE v2 GID for {netdev}/{local_ip}, found {matches}")
    gid_indexes.add(matches[0])

if len(gid_indexes) != 1:
    raise SystemExit(f"selected rails use different GID indexes: {gid_indexes}")

values = {
    "NCCL_IB_HCA": "=" + ",".join(hcas),
    "NCCL_IB_GID_INDEX": next(iter(gid_indexes)),
    "RDMA_PEER_NETDEVS": ",".join(netdevs),
    "FABRIC_MODE": mode,
}
if mode == "direct":
    # Keep NCCL/Gloo off mgmnt.10: the direct ConnectX rails carry both
    # bootstrap sockets and collectives. The management VLAN must remain
    # available for Kubernetes, JuiceFS metadata, and control traffic.
    values["NCCL_SOCKET_IFNAME"] = ",".join("=" + netdev for netdev in netdevs)
    values["GLOO_SOCKET_IFNAME"] = netdevs[0]
    values["RDMA_LOCAL_ADDRESS"] = local_addresses[0]
    values["RDMA_PEER_ADDRESS"] = peer_addresses[0]
    values["RDMA_PEER_NODE"] = links[0]["peerNode"]
else:
    # Routed: bootstrap and Gloo ride the control-plane interface; the peer
    # fabric address is its control IP (reachable via the mgmnt LAN), and
    # collectives resolve peer RoCE GIDs over the forwarded fabric hop.
    control_iface = fabric["controlPlane"]["interface"]
    values["NCCL_SOCKET_IFNAME"] = control_iface
    values["GLOO_SOCKET_IFNAME"] = control_iface
    values["RDMA_LOCAL_ADDRESS"] = host_ip
    values["RDMA_PEER_ADDRESS"] = peer_control_ip
    values["RDMA_PEER_NODE"] = CONTROL_NODE_BY_IP.get(peer_control_ip, "unknown")
for key, value in values.items():
    print(f"export {key}={shlex.quote(value)}")
PY
)"

# Fail cleanly instead of tripping `set -u` on the summary line below when
# discovery aborted (was: "RDMA_PEER_NODE: unbound variable" hiding the real
# error).
[ -n "${RDMA_PEER_NODE:-}" ] || { echo "fabric discovery failed for peer $PEER_CONTROL_IP" >&2; exit 1; }

if [ "$FABRIC_MODE" = routed ]; then
  # Preflight the routed fabric path: at least one static route to a fabric
  # subnet we are not on, egressing one of our fabric interfaces.
  if ! python3 - "$inventory" <<'PY'
import ipaddress
import json
import pathlib
import subprocess
import sys

fabric = json.loads(pathlib.Path(sys.argv[1]).read_text())
local = {ipaddress.ip_interface(l["address"]).network for l in fabric["links"]}
own = {l["interface"] for l in fabric["links"]}
routes = subprocess.run(["ip", "-4", "route", "show"], capture_output=True, text=True).stdout
for line in routes.splitlines():
    fields = line.split()
    if not fields or "/" not in fields[0]:
        continue
    dest = fields[0]
    if "via" not in fields or "dev" not in fields:
        continue
    dev = fields[fields.index("dev") + 1]
    if dev in own and ipaddress.ip_network(dest, strict=False) not in local:
        raise SystemExit(0)
raise SystemExit(
    "routed fabric preflight failed: no route to a non-local fabric subnet via a fabric interface "
    "(deploy dotfiles routed-RoCE config or pin the lane to an adjacent pair)"
)
PY
  then
    exit 1
  fi
fi

echo "fabric mode=$FABRIC_MODE peer=$RDMA_PEER_NODE control=$PEER_CONTROL_IP rails=${RDMA_PEER_NETDEVS:-none} hcas=$NCCL_IB_HCA gid=$NCCL_IB_GID_INDEX"
