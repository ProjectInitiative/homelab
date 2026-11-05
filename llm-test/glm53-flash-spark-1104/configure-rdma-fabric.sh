#!/bin/bash
# Same discovery contract as the glm53 EXL3 lane: validate the node-local
# inventory against this pod's node/host, then export NCCL env selecting
# the peer-facing RoCE rails. TensorFold drives collectives through NCCL,
# and patch 0006's RoCE proxy reads TF_ROCE_HCA / TF_ROCE_GID_INDEX with
# NCCL_IB_HCA / NCCL_IB_GID_INDEX fallbacks — all covered by these exports.
# Only the recipe's measured-minimal NCCL set is exported; extra NCCL
# tuning knobs kept NCCL on one rail upstream and are deliberately omitted.
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
links = [
    link for link in fabric["links"]
    if link["peerControlAddress"] == peer_control_ip
]
if len(links) != 2:
    raise SystemExit(
        f"expected two rails to peer {peer_control_ip}, found {len(links)}"
    )

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
    # Keep NCCL/Gloo off mgmnt.10: the direct ConnectX rails carry both
    # bootstrap sockets and collectives. The management VLAN must remain
    # available for Kubernetes, JuiceFS metadata, and control traffic.
    "NCCL_SOCKET_IFNAME": ",".join("=" + netdev for netdev in netdevs),
    "GLOO_SOCKET_IFNAME": netdevs[0],
    "RDMA_LOCAL_ADDRESS": local_addresses[0],
    "RDMA_PEER_ADDRESS": peer_addresses[0],
    "RDMA_PEER_NODE": links[0]["peerNode"],
    "RDMA_PEER_NETDEVS": ",".join(netdevs),
}
for key, value in values.items():
    print(f"export {key}={shlex.quote(value)}")
PY
)"

echo "fabric peer=$RDMA_PEER_NODE control=$PEER_CONTROL_IP rails=$RDMA_PEER_NETDEVS hcas=$NCCL_IB_HCA gid=$NCCL_IB_GID_INDEX"
