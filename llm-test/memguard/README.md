# memguard-dgx — memory watchdog + forensics for the DGX Spark nodes

Privileged, hostPID DaemonSet (`memguard-daemonset.yaml`) that runs on every
`gpu=dgx-spark` node and watches the **host's** `MemAvailable` — the only view
that sees GB10 unified-memory truth. Context: RISK-0040 (TensorFold GLM lane
OOMs as chats approach the 512k window; cgroup working sets show ~8 GiB for an
~85 GiB rank, so Kubernetes memory limits are structurally blind there).

## What it does

1. **Time-series** — every loop (10 s normal, 3 s under pressure) logs
   `mem avail=<GiB> level=<0-3> top1=<top private-dirty process>`.
2. **Escalation snapshots** — crossing a threshold (or every 60 s while
   elevated) dumps full attribution: meminfo, PSI, top-15 processes by
   Private_Dirty, lane processes' detailed smaps_rollup, top container
   cgroups, top slab entries.
3. **PRE-KILL snapshot, then SIGKILL** — when MemAvailable < `KILL_GIB`
   (2.5 GiB) for `HOLD_S` (4 s), or < `HARD_GIB` (1 GiB) instantly, it takes
   a final PRE-KILL snapshot (the answer to "what was actually eating
   memory") and kills the lane rank processes on that node. The other rank
   notices the loss and exits; Conductor's `RecreateTogether` recreates the
   pair. **No conductor change is required** — the recovery path already
   exists (RISK-0040).

## Reading the output

```bash
kubectl logs -n llm-test -l app=memguard-dgx --tail=2000
# survives pod restarts, 20 MiB rotating:
kubectl exec -n llm-test ds/memguard-dgx -- tail -200 /var/lib/llm-test/memguard/history.log
```

Interpreting the PRE-KILL snapshot (this is the RISK-0040 investigation):

| Finding | Meaning | Fix |
|---|---|---|
| Rank `Private_Dirty` grown by tens of GiB | engine-internal growth (prompt workspaces, kept prompt states `TF_GLM_CACHE_ENTRIES=32`, CUDA graphs) | tune profile: raise reserve, lower context/parallel, fewer cache entries |
| MemAvailable fell but **no** process accounting grew | driver/UMA allocations outside process RSS | raise `TENSORFOLD_MEMORY_RESERVE_GIB`; report upstream with the snapshot |
| Another pod's cgroup memory.current grew | neighbor workload (gcache ring mount pod, VM, juicefs) | conductor priority policy / move the neighbor |
| Slab/SUnreclaim huge | kernel memory pressure | kernel tuning, report |

## Knobs (DaemonSet env, restart the DS to apply)

| Env | Default | Meaning |
|---|---|---|
| `WARN_GIB` | 8 | MemAvailable below this → fast sampling + periodic snapshots |
| `KILL_GIB` | 2.5 | sustained floor (recipe `MEMGUARD_GIB`) |
| `HOLD_S` | 4 | seconds under `KILL_GIB` before kill (recipe `MEMGUARD_HOLD_S`) |
| `HARD_GIB` | 1 | instant-kill floor (recipe `MEMGUARD_HARD_GIB`) |
| `KILL_ENABLED` | 1 | `0` = pure observation (logs `WOULD KILL`, never kills) |
| `INTERVAL` / `FAST_INTERVAL` | 10 / 3 | sampling cadence, seconds |
| `SNAPSHOT_EVERY` | 60 | snapshot cadence while elevated, seconds |

To run in observation-only mode first:

```bash
kubectl -n llm-test set env ds/memguard-dgx KILL_ENABLED=0
```

## Deploy

```bash
kubectl apply -f llm-test/memguard/memguard-daemonset.yaml
kubectl get pods -n llm-test -l app=memguard-dgx -o wide
```

debian:bookworm-slim (multi-arch, ~30 MB) — safe even on sextant's
disk-pressure'd image filesystem.

## Why not inside the Conductor controller

The controller runs cluster-side and can only see kubelet/metrics-API memory —
the exact view proven blind to UMA. Attribution requires node-local
`/proc/*/smaps_rollup` and `/sys/fs/cgroup`. The division of labor:
memguard (node-local) detects + kills + records; Conductor (cluster-side)
sees the resulting container death and runs `RecreateTogether` recovery. A
future Conductor enhancement could surface memguard kill events in workload
status, but nothing in the recovery path needs it today.
