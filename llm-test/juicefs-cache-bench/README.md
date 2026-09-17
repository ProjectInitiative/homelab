# JuiceFS local-cache latency and IOPS harness

A Python controller provisions one ephemeral PVC at a time from a declarative
StorageClass matrix, seeds and explicitly evicts an 8 GiB test dataset, warms
every byte into a per-volume host-NVMe JuiceFS cache, executes randomized
repeated fio patterns, persists incremental results, and foreground-deletes
the child resources.

The default target is **astrolabe**, so the currently active DSV41 workload on
chronometer/sextant is not disturbed. The image is multi-architecture for a
future controlled Spark run after the serving lane is stopped.

## Corrections to the proposed matrix

JuiceFS CE 1.3.1 does not expose a `--max-threads` mount flag. Using it would
make the Mount Pod fail. The harness substitutes the supported
`max-fuse-io=1M` dispatch-size profile. CSI mount options omit CLI `--`
prefixes. Direct I/O is requested correctly by fio with `O_DIRECT`; the supported
FUSE-side capability for concurrent direct requests is `async_dio`. Every CSI
Mount Pod is pinned to JuiceFS CE 1.3.1 so the tested client cannot float.

References:

- [JuiceFS mount and warmup command reference](https://juicefs.com/docs/community/command_reference/)
- [JuiceFS cache behavior](https://juicefs.com/docs/community/guide/cache/)
- [CSI mount options](https://juicefs.com/docs/csi/guide/configurations/#mount-options)

## Profiles

1. `control`: clean JuiceFS defaults.
2. `direct`: adds the FUSE `async_dio` capability (all profiles use application `O_DIRECT`).
3. `meta`: 24-hour attr, entry, directory-entry, open-file, and readdir caches.
4. `fuse1m`: `max-fuse-io=1M`.
5. `stripped`: `prefetch=0,max-readahead=0`.
6. `meta-direct`: metadata cache and direct-I/O interaction.
7. `combined`: metadata + direct I/O + 1 MiB FUSE + stripped read-ahead.

All profiles use a distinct `/mnt/pool/juicefs-bench/<profile>` host directory for
profile isolation, a 32 GiB cache cap, a 5% free-space floor, and unique test
data. Astrolabe is currently about 91% full, so the default 10% floor disables
warming entirely. Test blocks are evicted before warmup and again during
cleanup.

## Access patterns

- 4 KiB random read, `psync`, QD1, one job.
- 4 KiB random read, `libaio`, QD64, four jobs.
- 4 MiB sequential read, `libaio`, QD16, four jobs.

Every measured fio read uses `--direct=1`, so Linux page cache cannot absorb
the dataset and compete with unified model memory. Each pattern runs three
times for 30 seconds after a five-second ramp. Execution order is shuffled
with a recorded deterministic seed. Results include mean/stdev/CV IOPS, mean
latency, p95/p99 latency, and bandwidth.

## Cleanup and results

Every spawned seed/warmup, fio, and cleanup Job uses
`ttlSecondsAfterFinished: 60`. The controller reads logs first and then deletes
the Job and PVC immediately with foreground propagation. Child Jobs and PVCs also
carry owner references to the controller, providing eventual garbage
collection if the controller is interrupted. Approved StorageClasses remain
declarative and persistent, avoiding cluster-scoped RBAC in the workload. The
controller Job uses the repository-wide three-day TTL.

Incremental output survives controller cleanup in:

```text
ConfigMap/juicefs-cache-bench-<run-id>
  results.md
  samples.json
  failures.json
```

Retrieve the latest table with:

```bash
name=$(kubectl get configmap -n llm-test \
  -l app=juicefs-cache-bench-results \
  --sort-by=.metadata.creationTimestamp \
  -o jsonpath='{.items[-1:].metadata.name}')
kubectl get configmap -n llm-test "$name" -o jsonpath='{.data.results\.md}'
```

## Launch

The tracked controller is suspended by default:

```bash
kubectl apply -f llm-test/juicefs-cache-bench/storageclasses.yaml
kubectl apply -f llm-test/juicefs-cache-bench/benchmark.yaml
kubectl patch job juicefs-cache-bench-v1 -n llm-test \
  --type=merge -p '{"spec":{"suspend":false}}'
kubectl logs -n llm-test -f job/juicefs-cache-bench-v1
```

For a short smoke test, change `PROFILE_FILTER=control`,
`RUNTIME_SECONDS=5`, `RAMP_SECONDS=1`, `REPETITIONS=1`, and `DATASET_GIB=4`,
then use a new versioned Job name. Jobs are immutable after creation.

The full matrix writes 56 GiB of unique seed data, then performs time-based
reads through the shared JuiceFS metadata/object-storage backend. Although node
placement isolates CPU, RAM, and NVMe from DSV41, run the full matrix only when
backend latency is not critical. Start with the control-only smoke profile.
