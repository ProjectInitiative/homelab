# JuiceFS DGX cache ring: implementation, incidents, and follow-up

Status: operationally deployed, peer-read validation still incomplete
Last updated: 2026-10-24

## Scope

This document records the TensorFold/ JuiceFS cache-ring work on the three DGX
Sparks in the `mc` cluster:

- `chronometer`: ConnectX addresses `172.16.5.55`, `172.16.6.55`, `172.16.7.55`, `172.16.8.55`
- `sextant`: `172.16.5.56`, `172.16.6.56`, `172.16.9.56`, `172.16.10.56`
- `octant`: `172.16.7.57`, `172.16.8.57`, `172.16.9.57`, `172.16.10.57`

The goal was to preserve existing caches and Garage fallback while enabling
JuiceFS gcache peer traffic over the switchless 200G ConnectX fabric. The
separate future goal is strict sharded cache ownership; that is not yet
implemented by the current local-cache integration.

## Starting problem

TensorFold readiness failures were initially suspected to be container or
model-serving crashes. They were actually model-loading reads blocked behind
JuiceFS/FUSE. The checkpoint was already present in the shared cache: 83
shards, 175,642,267,944 bytes. When peer routing or the mount path was wrong,
processes could enter kernel `D` state during FUSE reads and the health endpoint
never became ready.

Existing local caches were intentionally preserved (approximately 298 GiB on
chronometer, 501 GiB on octant, and 317 GiB on sextant at the time). No
`juicefs gc` or destructive cache cleanup was used.

## Durable configuration and code changes

1. A fixed JuiceFS CSI image was built from JuiceFS commit
   `8d8935ec0e2d37c31e4e7dd9ea318012265bc418`.
2. The CSI image was fixed for the mount script's Bash ANSI-C quoting by
   linking `/bin/sh` to `/bin/bash`. The original failure was:
   `fusermount3: unknown option '$cache-dir=/mnt/pool/juicefs-ring'`.
3. `CSIDriver/csi.juicefs.com` was made durable with
   `attachRequired: false` and `podInfoOnMount: true`.
4. The `model-cache` PVC was labeled
   `juicefs-cache-group: dgx-model-cache`.
5. Ring mounts use `/mnt/pool/juicefs-ring`, leaving the older
   `/mnt/pool/juicefs` cache path available for rollback.
6. Ring peer traffic uses host networking and TCP port `13910`. Port `3910`
   collided with other services and caused an ephemeral fallback in an earlier
   attempt.
7. The JuiceFS fork already supported semicolon-separated multi-rail
   advertisements in `pkg/gcache/manager.go`.
8. CSI `mountPodPatch` entries were consolidated to one labeled cache-ring
   patch. The former three node-specific entries were not safely node-specific:
   matching entries merged, and live mount pods inherited the wrong list,
   including octant's list on other nodes.
9. JuiceFS commit `d4c5a8eb` added `group-advertise=auto-c7`. The mount process
   discovers IPv4 addresses on active `enp*`, `enP*`, and `ib*` interfaces and
   advertises them as semicolon-separated `host:13910` endpoints. This avoids
   CSI patch-merge ambiguity while retaining node-local ConnectX addresses.

Relevant durable files:

- `clusters/mc.yaml`
- `bootstrap/base/juicefs-platform/csidriver.yaml`
- `bootstrap/base/juicefs-platform/node-config.yaml`
- `bootstrap/base/juicefs-platform/kustomization.yaml`
- `bootstrap/base/juicefs-platform/`
- JuiceFS fork: `pkg/gcache/manager.go`
- Prior validation references in the JuiceFS fork:
  `hack/gcache-smoke-test.sh`, `deploy/gcache-test/gcache-test.yaml`, and
  `deploy/gcache-test/SPARKS-TEST-DESIGN.md`

## Build and deployment history, including mistakes

### Image/build mistakes

- A local cross-platform Docker build failed with `exec /bin/sh: no such file
  or directory` while trying to build the ARM image through the local builder.
- A native remote Podman build succeeded on chronometer, but pushing from that
  session timed out. It was not used as the final deployment artifact.
- The first in-cluster BuildKit Job omitted ARM64 node affinity. It scheduled
  on `capstan1` and published an amd64 image under an ARM-looking tag. When the
  ring mounts consumed it, all three failed with:
  `exec /usr/bin/sh: exec format error`.
- The build Job was corrected with required `kubernetes.io/arch=arm64`
  affinity and rebuilt as:
  `local-registry.registry.svc.cluster.local:5000/homelab/juicefs-gcache-csi:8d8935ec-auto-c7-arm64@sha256:9296bb2ab09b938862ab7bb0fe3ce86400707d7fd4e0838565751713ef30a39e`.

### GitOps/Argo mistakes and recovery

- The local `dev` branch was ahead of the repository's `main`; the root Argo
  Application follows `HEAD`/main. A direct push to main was rejected by the
  repository rule requiring pull requests.
- Homelab PR #240 merged the initial `auto-c7` configuration. Homelab PR #241
  corrected the native ARM64 image pin. Both are merged.
- The JuiceFS fork change merged as PR #1.
- Argo initially held an old generated Application and later failed target
  synchronization because its connection to `172.16.1.50:6443` timed out or
  returned `no route to host`. The generated `juicefs-csi-driver` Application
  was refreshed/applied directly to the control cluster while connectivity was
  unstable; GitOps remains the source of truth.
- Argo reports a shared-resource warning because `CSIDriver/csi.juicefs.com`
  is referenced by both `juicefs-csi-driver` and `juicefs-platform`. This is
  noisy but not the cache-ring failure.

### Mount/reboot mess

- Deleting old ring mount pods while the TensorFold/FUSE consumers and CSI
  state were not fully quiesced caused CSI replacement loops. Octant showed
  `function timeout`, `mount point is not ready in 60s`, and
  `transport endpoint is not connected`.
- CSI repeatedly created and deleted replacement pods because the target path
  was stale or disconnected. The node itself was Ready, had no taints, and had
  no memory/disk/PID pressure.
- Octant also had a separate `gcache-test` JuiceFS mount on port `3910`; this
  was not the ring listener on `13910`. An earlier dmesg snapshot showed an
  OOM kill in that test workload, adding noise but not identifying the CSI
  ring root cause.
- Rebooting all three DGX nodes cleared the stale FUSE/kubelet state. After
  reboot, all three nodes became Ready and the ring mounts recreated cleanly.

## Current observed state

At the latest validation:

- `chronometer`, `sextant`, and `octant`: Ready
- Argo `juicefs-csi-driver`: Synced / Healthy / Succeeded
- All three cache-ring mount pods: Running
- All three use the native ARM64 digest above
- All three use `group-listen=:13910` and `group-advertise=auto-c7`
- Directly connected ConnectX TCP paths on port `13910` passed for the active
  chronometer/sextant pair; octant was not listening until its mount was
  successfully recreated after reboot.
- The preserved cache sizes observed during the work were uneven: roughly
  11 GiB chronometer, 3.7 GiB sextant, and 182 GiB octant. This is expected
  from preserved history and does not prove that all nodes downloaded the full
  model.

The last workload snapshot showed TensorFold v14 head Running but not Ready
and the worker in Error. That is a separate serving/readiness issue and must
not be treated as proof of gcache peer success.

## What gcache currently does

The current implementation uses rendezvous hashing to assign each block key to
an owner. On a full-block miss:

1. A mount checks its local disk cache first.
2. The block's ring owner is selected.
3. A non-owner requests the block from that owner over the peer network.
4. If the owner does not have the block, the owner fills it from Garage and
   serves it.
5. The receiving mount's normal `cachedStore` path caches the returned block
   locally.
6. Any peer failure falls back to Garage.

Therefore the current ring reduces repeated Garage reads and enables high-speed
peer sharing, but it does not enforce one physical disk copy per block. A
non-owner's peer-fetched block can also be written into its local disk cache.
If every node reads every model block, local caches can converge toward a full
model on every node even though ownership and origin fetches are sharded.

Also, member UUIDs are fresh per mount process. A reboot/remount can change
ownership assignments, so preserved cache files from an older membership view
do not necessarily correspond to the current owner of each key.

## Future strict sharded ownership design

Keep this as a backburner item; do not change the current ring during serving
recovery.

Desired behavior:

- One member is authoritative for each block according to rendezvous hashing.
- The owner stores/fills the persistent disk copy.
- Non-owners fetch over ConnectX without permanently writing peer-fetched
  blocks into their persistent disk caches, or use an explicit consumer mode
  with `cache-size=0`.
- Peer metrics prove owner reads, peer fetches, fallback reads, and failover.
- Membership changes move only the expected fraction of keys and do not require
  cache cleanup.

Possible implementations:

1. Run non-owner/consumer mounts with `cache-size=0` while keeping peer reads;
   this is operationally simpler but trades disk savings for repeated peer
   traffic and page-cache behavior.
2. Add a cache-layer distinction between object-store fills and peer fills so
   peer responses can be served without persistent local disk insertion.
3. Add explicit owner-only fill/push behavior and a test that verifies one-copy
   placement, owner reassignment, failover, and no accidental duplicate disk
   growth.

Acceptance tests should include:

- membership registry contains exactly three live members;
- each member advertises only its local ConnectX addresses;
- checksum-identical cross-node reads;
- nonzero `juicefs_remotecache_gets` and `juicefs_remotecache_bytes`;
- peer byte counts match serving-side accounting;
- Garage fallback works when an owner is stopped;
- ring growth/reassignment moves approximately the expected fraction of keys;
- persistent cache growth demonstrates the intended one-copy/sharded policy.

## Operational cautions

- Do not delete ring mount pods while consumers are actively using the PVC
  unless the workload is deliberately quiesced and CSI cleanup is watched.
- Do not clean the preserved caches or run `juicefs gc` as a ring fix.
- Do not declare success from Ready mount pods alone; prove peer reads with
  metrics and checksums.
- Keep the firewall enabled; the DGX ConnectX interfaces are trusted by the
  NixOS host policy. Troubleshoot topology, address advertisement, port
  conflicts, and CSI lifecycle instead.
- Keep TensorFold scaled down or isolated until the peer-read test and mount
  lifecycle are clean.
