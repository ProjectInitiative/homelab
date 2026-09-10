# CubeFS vs JuiceFS: architecture, deployment, caching, and RDMA

> Scope: CubeFS master documentation and JuiceFS Community/Enterprise documentation. Product capabilities and licensing change; verify the target release before deployment.

## Executive summary

- **CubeFS is a storage system first.** Its normal deployment owns the data plane: MetaNodes store metadata and DataNodes store replicated file data. Its ObjectNode is an S3-compatible *gateway* over CubeFS data; CubeFS does not require S3 as its backend.
- **JuiceFS is a filesystem layer over a metadata service and object storage.** The object store is the durable data backend, while the metadata engine stores filesystem metadata. In this repository, JuiceFS uses TiKV for metadata and Garage for S3-compatible object storage.
- **Both now have distributed-cache concepts**, but they are different products/features. CubeFS Flash is an integrated distributed cache using FlashNodes/FlashGroups and a consistent-hash ring. JuiceFS distributed cache is a set of JuiceFS clients/cache nodes sharing blocks, with object storage as the fallback/source of truth.
- **RDMA is not equivalent in the two systems.** CubeFS documents a beta RDMA path primarily accelerating client-to-DataNode file I/O (especially writes). JuiceFS Enterprise 5.3 documents RDMA specifically for the distributed-cache data path between clients and cache nodes. JuiceFS Community does not provide the Enterprise distributed-cache/RDMA feature.
- **For the stated goal—RDMA plus distributed caching for GPU/AI workloads—JuiceFS Enterprise is the direct fit**, but it requires licensing and a supported `mount.rdma` binary. CubeFS is the credible open-source alternative to evaluate if operating a complete storage cluster and using its Flash cache is acceptable; its documented RDMA path and cache integration need release-level validation rather than being treated as a drop-in equivalent.

## 1. What CubeFS is and how it is set up

### Core architecture

CubeFS has several storage subsystems:

| Component | Role | Typical deployment |
|---|---|---|
| Master | Cluster/resource management and volume topology | StatefulSet, normally 3 replicas |
| MetaNode | File metadata | At least 3 nodes recommended |
| DataNode | File contents, normally replicated | At least 3 nodes; disk-dense hosts |
| ObjectNode | Stateless S3-compatible object gateway | Deployment; optional if only POSIX is needed |
| BlobStore / BlobNode | Optional erasure-coded key/value storage subsystem | Separate EC-oriented component set |
| Client / CSI | POSIX client and Kubernetes integration | Client mounts or CSI deployment |
| FlashNode / FlashGroup | Distributed cache (Flash feature) | Cache nodes grouped into hash-ring groups |

The official Kubernetes deployment guide says to use a Kubernetes cluster with at least three nodes (four or more preferred), label nodes by role, and expose local disks through `hostPath`. Master, MetaNode, and DataNode use host networking in that deployment model. DataNode hosts must have formatted and mounted disks; the example uses XFS and `/data0`, `/data1`, etc. [CubeFS Kubernetes deployment](https://cubefs.io/docs/master/deploy/k8s.html)

A representative Helm deployment is:

```bash
git clone https://github.com/cubefs/cubefs-helm.git
helm upgrade --install cubefs ./cubefs \
  -f cubefs-helm.yaml -n cubefs --create-namespace
```

The guide's example uses three Masters, three ObjectNodes, three or more MetaNodes/DataNodes, host paths for metadata/logs, and one or more DataNode disks. The actual values file is the source of truth for ports, resource limits, scheduling, and component configuration.

### Does CubeFS use S3 on the backend?

**No—not in the JuiceFS sense.** CubeFS's S3 support is an access protocol:

```text
S3 client -> ObjectNode -> MetaNode + DataNode/BlobStore -> CubeFS-managed disks
POSIX client ----------------^                       
```

ObjectNode translates S3 buckets/keys into CubeFS volumes/paths. It obtains topology from Master and communicates directly with MetaNodes and DataNodes. It is stateless and can scale horizontally. The S3 signature model is compatible with Amazon S3 SDKs, but CubeFS still stores the data in its own storage cluster. See [CubeFS Object Gateway](https://cubefs.io/docs/master/design/objectnode.html).

Therefore, installing CubeFS normally means provisioning:

1. Kubernetes or VMs for the control and storage services.
2. Dedicated, persistently mounted disks for DataNodes (and high-performance storage for metadata where appropriate).
3. Network connectivity between Masters, MetaNodes, DataNodes, ObjectNodes, and clients.
4. Replication or EC policy, failure domains/AZ placement, capacity reservations, monitoring, repair, and upgrade procedures.
5. Users/volumes and S3 credentials if ObjectNode will be used.

CubeFS also has BlobStore, an independent erasure-coded subsystem. It uses Reed–Solomon schemes such as `6+3`, `12+3`, and `10+4`, with ClusterManager metadata and BlobNodes holding chunks. This is still CubeFS-managed storage, not an external S3 backend. See [BlobStore design](https://cubefs.io/docs/master/design/blobstore.html).

### CubeFS durability and performance model

The traditional file path uses multiple replicas. BlobStore offers online EC to reduce storage overhead. EC trades lower capacity cost for encoding/decoding CPU, fan-out, and possible read amplification—especially for small files. It supports multi-AZ layouts and asynchronous repair. This makes CubeFS closer to a complete distributed storage appliance than to a filesystem client backed by an object store.

Important operational implications:

- You own disk lifecycle, replacement, rebalancing, data repair, and capacity planning.
- ObjectNode does not make CubeFS an S3-native backend; it is an S3-compatible frontend.
- S3 and POSIX are intentionally unified over the same underlying namespace. This has semantic differences from native object storage: for example, keys that would coexist in S3 can conflict when mapped to POSIX files/directories. [Object Gateway naming caveat](https://cubefs.io/docs/master/design/objectnode.html#object-name-conflict-important)

## 2. CubeFS distributed cache and RDMA

### Flash distributed cache

CubeFS Flash addresses the same broad AI-training problem: datasets too large for one GPU node's local disk, but repeatedly read by many GPU nodes. Flash cache nodes are arranged into FlashGroups, which own ranges of a consistent-hash ring. Clients hash volume ID, inode, and offset to select the responsible group. A FlashGroup contains FlashNodes, potentially across zones; clients can select the lowest-latency FlashNode. The Master manages topology, registration, heartbeats, and slot assignment. [CubeFS Flash cluster](https://cubefs.io/docs/master/feature/flash.html)

The documented FlashNode configuration includes:

- Master addresses;
- cache memory percentage and read-RPS limits;
- one or more local cache disks;
- zone name;
- temporary filesystem enable/disable settings.

That is a real distributed cache, not merely DataNode replication. It is integrated with CubeFS's volume/client path and can be used to avoid repeatedly reading the durable storage tier.

### CubeFS RDMA

CubeFS also publishes an RDMA design/release path. The documented design focuses on **client-to-DataNode data transfer**, with control messages using send/receive and payloads using RDMA read/write. The write path lets the DataNode leader pull client buffers, persist them, and forward data to followers; the read path lets the DataNode write data directly into the client's registered buffer. [CubeFS RDMA design (wiki)](https://github.com/cubefs/cubefs/wiki/RDMA)

The public release is explicitly marked **beta** (`v3.4.0-beta-rdma`), and the design is not the same statement as “Flash distributed-cache data transfer uses RDMA.” Before selecting CubeFS for this requirement, validate:

- exact supported CubeFS release and client/server binary;
- RoCE/InfiniBand/verbs compatibility and NIC/driver requirements;
- whether RDMA applies to FlashNode cache traffic in the selected release, or only normal DataNode I/O;
- Kubernetes device/plugin, host-network, and memory-registration requirements;
- failure fallback behavior and observability.

## 3. What JuiceFS is and how it is set up

### Core architecture

JuiceFS separates metadata and data:

```text
POSIX client / CSI mount
        |
        +--> metadata engine (filesystem namespace, chunks, sessions)
        |
        +--> object storage (file data/chunks)
```

The client performs filesystem operations and manages local cache. The metadata service stores namespace and filesystem metadata. Durable file data is stored in an object-storage backend (S3-compatible or another supported backend). See [JuiceFS architecture](https://juicefs.com/docs/community/architecture/) and [JuiceFS introduction](https://juicefs.com/docs/community/introduction/).

This creates a useful operational split:

- Object storage supplies durable capacity and durability semantics.
- Metadata service supplies filesystem consistency/namespace state and must be sized and protected accordingly.
- Clients/cache nodes supply performance. Local cache loss is normally a performance event, not data loss.

### This repository's current JuiceFS topology

The repository already implements the basic JuiceFS pattern:

- `bootstrap/base/tikv-cluster/cluster.yaml`: a 3-PD/3-TiKV TiDB/TiKV cluster for JuiceFS metadata.
- `bootstrap/base/juicefs-platform/job-format.yaml`: formats the filesystem with `--storage`, `--bucket`, credentials, and `--metaurl`; it optionally uses an RSA key or passphrase.
- `apps.yaml`: deploys the JuiceFS CSI driver and obtains `juicefs-creds`/`juicefs-key` from OpenBao.
- `bootstrap/base/juicefs-platform/node-config.yaml`: configures CSI mount pods with local cache and a `dgx-spark` distributed-cache group on `chronometer` and `sextant`.

Current cache behavior is TCP distributed cache, not RDMA: the ConnectX subnet is left as a commented `group-ip` example and no `rdma-network` option is configured. `astrolabe` is deliberately local-cache-only because it has no fast east-west link. See [`node-config.yaml`](../bootstrap/base/juicefs-platform/node-config.yaml).

The current deployment requires, at minimum:

1. A metadata cluster (already represented by TiKV).
2. An S3-compatible backend (the repo's credentials contain storage/bucket/access key/secret key; the chosen backend is configured outside the shown format job).
3. JuiceFS format metadata and credentials in OpenBao.
4. JuiceFS CSI driver and mount pods on worker nodes.
5. Local cache disks and consistent cache sizing for distributed-cache members.
6. A private, reliable east-west network; JuiceFS recommends at least 10 GbE for distributed cache, with the fastest interface selected via `group-ip`.

## 4. JuiceFS caching and RDMA

### Community/local cache

JuiceFS Community supports per-client local caching. It does **not** provide the Enterprise distributed-cache/RDMA feature. A local cache is node-local and can be backed by SSD/NVMe or memory; misses read from object storage. This is simple and robust, but repeated reads by different nodes can cause repeated object-store downloads.

### Enterprise distributed cache

JuiceFS Enterprise distributed cache forms a cache group using a consistent-hashing ring. Each member is a normal JuiceFS mount; members with the same `--cache-group` share cache blocks. A miss is served by the owning peer when possible, otherwise the peer downloads from object storage. The client falls back to object storage if peer communication fails. [JuiceFS distributed cache](https://juicefs.com/docs/cloud/guide/distributed-cache/)

The documented deployment modes are:

```bash
# Cache provider node
juicefs mount NAME /distributed-cache \
  --cache-group=dgx-spark \
  --cache-dir=/data/distributed-cache \
  --cache-size=500000

# Application/client node: consume cache but do not serve cache
juicefs mount NAME /jfs \
  --cache-group=dgx-spark --no-sharing --cache-size=0
```

A dedicated cache cluster is usually preferable for Kubernetes because application pods/nodes scale and disappear. It also avoids ephemeral clients destabilizing the ring. Use homogeneous cache nodes and separate cache directories for separate mounts. Cache membership changes trigger rebalancing; node failures fall through to object storage, so cache is not the durability layer.

### Enterprise RDMA

JuiceFS Enterprise 5.3 adds RDMA specifically to the distributed-cache transfer path—between clients and cache nodes—not primarily to metadata traffic. Metadata remains ordinary control traffic over IP/TCP. [JuiceFS RDMA](https://juicefs.com/docs/cloud/guide/distributed-cache-rdma/)

Requirements called out by the documentation:

- RDMA-capable NICs on **both** client and cache-node endpoints;
- matching transport environment (for example, RoCE-to-RoCE or InfiniBand-to-InfiniBand);
- IPv4 addresses still configured for discovery/control;
- working RDMA connectivity and drivers;
- the Enterprise `mount.rdma` package/binary;
- `--rdma-network` on every participating cache server and client;
- `--group-network`/group IP for control traffic as appropriate.

Example shape:

```bash
# Enterprise RDMA cache provider
juicefs mount NAME /distributed-cache \
  --cache-group=dgx-spark \
  --rdma-network=ib0:ib2 \
  --cache-dir=/data/cache \
  --cache-size=-1 \
  --buffer-size=8192

# Enterprise RDMA consumer
juicefs mount NAME /jfs \
  --cache-group=dgx-spark --no-sharing \
  --rdma-network=ib0:ib1 \
  --cache-size=0 \
  --buffer-size=8192
```

The feature is documented as beta and targeted at networks above 100 Gb/s or workloads where storage I/O CPU use is material. It supports mixed RDMA/TCP clients, but specifying a bad RDMA NIC can cause startup failure rather than silently solving the problem. Validate with `rdma link` and `rping`; monitor remote-cache and RDMA metrics.

## 5. Side-by-side comparison

| Dimension | CubeFS | JuiceFS Community | JuiceFS Enterprise |
|---|---|---|---|
| Primary model | Complete distributed storage cluster | Filesystem over metadata + object storage | Same, plus proprietary performance features |
| Durable data | CubeFS DataNodes or BlobStore disks | External object storage | External object storage |
| S3 | ObjectNode frontend/gateway | Backend data store | Backend data store |
| POSIX + S3 same data | Yes, via ObjectNode mapping | Depends on object backend/access model | Same |
| Metadata | CubeFS Masters/MetaNodes (and BlobStore ClusterManager for EC) | External metadata engine | Same |
| Replication/EC | Native replica subsystem and BlobStore EC | Delegated mostly to object store | Same |
| Distributed cache | FlashNodes/FlashGroups, integrated | No Enterprise distributed cache | Consistent-hash cache group/dedicated cache cluster |
| RDMA | Public beta path focused on client/DataNode I/O; verify Flash applicability | No | RDMA cache path, documented in 5.3+ |
| Kubernetes | Helm; host network and hostPath disks in official guide; CSI available | CSI driver + mount pods | CSI/mount deployment plus Enterprise binary/config |
| Operational burden | High: operate storage servers/disks/repair | Lower storage burden; operate metadata and object store | Same, plus cache/RDMA platform |
| Storage cost model | You buy/manage disks; EC reduces overhead | Object-store capacity/pricing | Same |
| Best fit | Self-contained POSIX/S3 storage, control of disks, open stack | General Kubernetes filesystem and inexpensive object-backed durability | High-throughput shared-cache/GPU workloads where license is acceptable |

## 6. Recommendation for this homelab

### If the priority is the requested feature set

Stay with JuiceFS for the filesystem abstraction and evaluate **JuiceFS Enterprise** for the cache tier. It maps directly onto the desired design: existing TiKV metadata, existing S3-compatible backend, CSI integration, dedicated cache group, and RDMA only on the high-volume cache data path. The migration is primarily licensing, Enterprise image/binary availability, node networking, and CSI mount-option plumbing—not a replacement of the storage architecture.

A sensible target topology is:

```text
Garage/S3  <-- durable data
TiKV       <-- JuiceFS metadata
2+ stable cache nodes with NVMe + RDMA NICs
GPU/application clients with matching RDMA NICs
CSI mounts: cache providers + --no-sharing consumers
```

Do not enable RDMA until the ConnectX/RoCE or InfiniBand fabric is operational and tested end-to-end. Add `rdma-network` only to nodes that actually have the matching NIC and use a separate `group-ip`/control network if useful.

### When CubeFS is worth a proof of concept

Evaluate CubeFS if one or more of these are more important than minimizing operational work:

- you want to own the durable storage layer rather than depend on S3/Garage;
- you want one system exposing both POSIX and S3;
- you can provide disk-dense storage nodes and operate repair/rebalancing;
- Flash distributed cache is attractive and CubeFS's beta RDMA path meets the exact workload;
- you want native replica/EC choices rather than object-store durability.

For a fair benchmark, compare the same dataset and access pattern across: JuiceFS Community local cache, JuiceFS Enterprise TCP distributed cache, JuiceFS Enterprise RDMA distributed cache, and CubeFS POSIX/DataNode plus Flash cache. Measure warm-cache throughput, cold-cache object/backend reads, cache miss penalty, CPU per GiB/s, tail latency, ring/node failure behavior, rebalance time, and recovery after cache loss.

## Sources

- [CubeFS introduction](https://cubefs.io/docs/master/overview/introduction.html)
- [CubeFS architecture](https://cubefs.io/docs/master/overview/architecture.html)
- [CubeFS Kubernetes deployment](https://cubefs.io/docs/master/deploy/k8s.html)
- [CubeFS Object Gateway](https://cubefs.io/docs/master/design/objectnode.html)
- [CubeFS BlobStore/EC](https://cubefs.io/docs/master/design/blobstore.html)
- [CubeFS Flash distributed cache](https://cubefs.io/docs/master/feature/flash.html)
- [CubeFS RDMA design](https://github.com/cubefs/cubefs/wiki/RDMA)
- [CubeFS beta RDMA release](https://github.com/cubefs/cubefs/releases/tag/v3.4.0-beta_rdma)
- [JuiceFS Community architecture](https://juicefs.com/docs/community/architecture/)
- [JuiceFS Community cache](https://juicefs.com/docs/community/guide/cache/)
- [JuiceFS Enterprise distributed cache](https://juicefs.com/docs/cloud/guide/distributed-cache/)
- [JuiceFS Enterprise RDMA](https://juicefs.com/docs/cloud/guide/distributed-cache-rdma/)
- Repository implementation: [`bootstrap/base/juicefs-platform/node-config.yaml`](../bootstrap/base/juicefs-platform/node-config.yaml), [`job-format.yaml`](../bootstrap/base/juicefs-platform/job-format.yaml), [`tikv-cluster/cluster.yaml`](../bootstrap/base/tikv-cluster/cluster.yaml), and [`apps.yaml`](../apps.yaml)
