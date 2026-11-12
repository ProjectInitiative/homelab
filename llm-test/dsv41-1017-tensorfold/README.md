# DeepSeek-V4.1-Flash-1017 TensorFold lane (2× DGX Spark, TP=2) — STAGED

Kubernetes port of
[MiaAI-Lab/DeepSeek-v4.1-Flash-1017-2x-DGX-Sparks](https://github.com/MiaAI-Lab/DeepSeek-v4.1-Flash-1017-2x-DGX-Sparks)
@ `d8e5b28d`: the **1017 checkpoint** (39-shard EXL3 EAQ v1 2.9 bpw, ~196 GiB)
on **TensorFold's native Zig engine** (BertholomusAI dsv41 family), TP=2 with
one rank per Spark, full 1,048,576-token window, DSpark drafting, OpenAI API on
**port 8888**. This is a *different runtime* from the existing
`dsv41-parity/` lane (old checkpoint, vLLM) and from `tensorfold-glm53-v14/`
(GLM, same engine family — its structure is what this lane clones).

**Status: STAGED, NOTHING DEPLOYED.** Deployments ship `replicas: 0`; the
Conductor ManagedWorkload ships `desiredState: Standby`; the download Job ships
`suspend: true`.

## Immutable pins

| Item | Pin |
|---|---|
| Recipe | `MiaAI-Lab/DeepSeek-v4.1-Flash-1017-2x-DGX-Sparks @ d8e5b28da6ebcf539035be564a4a94d087b2f480` |
| Engine | TensorFold fork `bertholomus/TensorFold` branch `deepseek-v41-zig @ 629c524a` + inputs `@ 59402086`; Zig 0.17.0; 33+2 recipe patches |
| Image | built by `01-image-build.yaml` → `local-registry.../homelab/tensorfold-dsv41-1017:exl3-tp2-2b94be4562b1` (config.sh `image_hash()`; ~24.9 GB) — **pin the digest in all manifests after build** |
| Checkpoint | `Mia-AiLab/DeepSeek-V4.1-Flash-1017-EXL3-EAQ-v1-2.9-bpw @ 45ee5d0f` (39 shards, 210,601,036,966 bytes) |
| Engram | `deepseek-ai/DeepSeek-V4.1-Flash-1017 @ 1bae0e10` — only shards 47+48 (~203 GB; sha256 cross-checked against the recipe's card constants) |
| Kernel kit | `bertholomus/deepseek-v4.1-tensorfold-tp2-2xgb10 @ abe07c7d` (RoPE tables + routing bias generated from the checkpoint, MANIFEST-verified) |
| Served id / port | `DeepSeek-V4.1-Flash-1017` / 8888 |
| Rendezvous | TF_TP_PORT 29620 (dsv41-lane-unique) |

## Files / apply order

| Order | File | What |
|---|---|---|
| 0 | `00-model-cache-ephemeral.yaml` | 3 TiB RWX PVC on `juicefs-cache-sc` (Garage bucket `juicefs-mc-cache`, dedicated `juicefs_cache` postgres DB — **not backed up**), labeled to inherit the gcache-ring mountPodPatch |
| 1 | `01-image-build.yaml` | Suspended rootless-BuildKit Job (native arm64, prefers octant); builds + pushes the engine image |
| 2 | `02-checksums.yaml` | Immutable SHA-256 inventory (67 files) for both HF pins |
| 3 | `03-download-model.yaml` | Suspended puller-v6 Job: checkpoint + Engram shards into the ephemeral PVC; resumable; writes `/models/.dsv41-1017-download-complete` receipt |
| 4 | `04-gcache-ring-bench.yaml` | Engram storage gate bench (see below) |
| 5 | `05-prepare-model-tree.yaml` | Recipe prepare.sh steps 4–5: kit clone + verify, RoPE tables, routing bias, token map, **both ranks'** ~99 GiB rank-cache weight files, served tree. Writes `/models/.dsv41-1017-prep-complete` |
| 6 | `10-dsv41-1017-tensorfold.yaml` | verify/reclaim init gates + `dsv41-1017-worker` / `dsv41-1017-head` Deployments (replicas 0) + rendezvous Services |
| 7 | `11-services.yaml` | `dsv41-1017-head` API Service :8888 |
| 8 | `../conductor-workloads/deepseek-v41-1017.yaml` | ManagedWorkload CRD — Conductor picks it up in Standby |

## Engram placement gate (the open question)

**Does this version need Engram on fast local storage? Yes, per all evidence
so far — but the gcache ring might close the gap, so we test before packing.**

- The recipe is explicit: Engram tables must be on **local disk on both
  Sparks**. Head reading them over NFS: ~940 µs per random 4 KiB read vs ~90 µs
  local → prefill collapses to ~690–890 tok/s (vs ~2000+). A decode round makes
  ~70 random 4 KiB Engram row reads (`scripts/config.sh`).
- Our own dsv41-parity validation measured **fully warmed JuiceFS at 380–434
  random 4 KiB IOPS (2.3–2.6 ms)** vs 12.8–13.4k IOPS on raw NVMe, and serving
  plateaued at 4.2 tok/s until Engram was packed to node-local NVMe.

`04-gcache-ring-bench.yaml` measures the *actual* serving configuration (same
StorageClass, same PVC label → same gcache-ring mount options) on octant:

1. `kubectl apply -f 04-gcache-ring-bench.yaml` (not suspended)
2. Read the fio JSON lines from `kubectl logs -n llm-test job/dsv41-1017-gcache-engram-bench-v1 -c fio`
3. **PASS** if 4k QD1 psync shows mean latency ≤ 200 µs AND ≥ 5,000 IOPS →
   keep Engram on JuiceFS as staged.
4. **FAIL** → run the node-local pack fallback (below) and swap the mounts.

**Node-local pack fallback** (mirrors `dsv41-parity/07-pack-engram-local.yaml`):
create retained `local-path-nvme-sticky` PV/PVC pairs (node-affine, ~310 GiB
each: rank file ~99 GiB + Engram ~203 GB), run `tf-dsv41-rank-cache` /
hardlink-Engram prep jobs pinned per node, then change the Deployments:

- worker: mount the node-affine PVC at `/rank-cache` and Engram copy at
  `$ENGRAM` (a per-node copy of the two shards);
- head: mount its Engram copy for `TF_DS_ENGRAM`;
- drop the shared-PVC subPath mounts.

Note: with capability scheduling the fallback re-introduces de-facto node
pinning via PVC node affinity — acceptable; Conductor's RecreateTogether
recovery re-schedules the pair, and the retained sticky PVs keep data.

## Download lifecycle (deliberate, like tensorfold-v14)

```bash
kubectl apply -f 02-checksums.yaml -f 03-download-model.yaml
kubectl patch job dsv41-1017-model-pull-v1 -n llm-test --type=merge -p '{"spec":{"suspend":false}}'
kubectl logs -n llm-test -f job/dsv41-1017-model-pull-v1
```

Completion is valid only when the Job is Complete and the log reports all 67
inventory files, 39 shards / 210,601,036,966 bytes, and the receipt at
`/models/.dsv41-1017-download-complete`. Set `VERIFY_ALL_SHA=1` before
unsuspending to sha256 every shard (~+1 h of NVMe reads); by default the two
card-listed Engram shards and all metadata files are sha-verified, shards are
size-verified.

Then build the image, run prep, bench, and only then activate:

```bash
kubectl apply -f 01-image-build.yaml -f 05-prepare-model-tree.yaml -f 10-dsv41-1017-tensorfold.yaml -f 11-services.yaml -f ../conductor-workloads/deepseek-v41-1017.yaml
kubectl patch job dsv41-1017-image-build-v1 -n llm-test --type=merge -p '{"spec":{"suspend":false}}'
```

## Activation (Conductor cutover)

1. Confirm download + prep receipts, bench gate decided, image digest pinned.
2. `kubectl patch managedworkload deepseek-v41-1017 -n llm-test --type=merge -p '{"spec":{"desiredState":"Resident"}}'`
3. Conductor starts worker (rank 1) then head (rank 0); qualification polls
   `dsv41-1017-head/health` for up to 60 min (cold JuiceFS load).
4. Smoke: `curl http://<head>:8888/v1/chat/completions -d '{"model":"DeepSeek-V4.1-Flash-1017","max_tokens":16,"messages":[{"role":"user","content":"Reply OK."}]}'`
5. Router/LiteLLM cutover is a separate explicit step.

TP2 is **not elastic**: loss/recreation of either rank needs coordinated pair
recreation (head down → worker down → worker up → head up). Conductor's
`RecreateTogether` policy encodes this; the old lane's RISK-0018 reasoning
applies unchanged.

## Deliberate deltas vs the recipe (reviewer attention)

1. **NFS replaced by shared RWX JuiceFS + capability scheduling.** The recipe's
   worker reads HF_CACHE over NFS; here both ranks read the same ephemeral
   PVC. Rank-local heavy paths (rank-cache weight file, Engram) are subPaths of
   the shared PVC pending the bench gate. The recipe's own NFS numbers are the
   warning label for why the gate exists.
2. **Both rank files pre-generated on shared storage.** `tf-dsv41-rank-cache`
   is CPU-only; generating rank0+rank1 up front (~99 GiB each) avoids
   regenerating when Conductor swaps which node is head.
3. **Rendezvous rides the 172.16.4.x control plane** (`TF_TP_MASTER` =
   head pod's hostIP via the headless Service), not the CX7 link IP. The v1.4
   GLM TensorFold lane validated this pattern for TensorFold TP2. If the dsv41
   fork's rendezvous refuses non-link IPs, fall back to `TF_LOCAL_FABRIC_IP`
   (exported by the fabric script) + a mechanism to publish it to the worker.
4. **Chat template**: served tree links the checkpoint files and installs the
   recipe's `model/chat_template.jinja` (fetched at prep time, pinned rev);
   falls back to the checkpoint's own copy if the fetch fails. Verify
   `chat_template.jinja` after any checkpoint update.
5. **Memguard/port-patches/spill are not ported.** The recipe's
   `scripts/memguard.sh` host daemon is replaced by the init-gate MemAvailable
   check (112 GiB per `MIN_AVAIL_GIB`) + `llm-serving-critical` priority.
   Spill tiers default off (`SPILL_GIB` unset), `KV_SHARD` off — stock 1017
   profile. Ported-feature envs (`TF_DS_POOL`, `TF_DS_ROUND_ROWS`) are unset,
   matching recipe defaults.
6. **Image tag is self-verifying**: `exl3-tp2-<image_hash>` where image_hash is
   config.sh's own digest over pins+patches+Dockerfile. The build job
   recomputes it; a mismatch aborts. Pin the pushed **digest** afterwards.
7. **Recipe HEAD may have moved**: `d8e5b28d` is the reviewed snapshot from
   2026-10; if upstream moved, re-verify pins (config.sh) before rebuilding.

## Legacy `model-cache` retirement (the cutover you asked for)

**No data migration.** `llm-test/model-cache-migrate-ephemeral.yaml` (the
2 TiB copy job) is NOT part of this plan — the 1017 lane re-downloads into
`model-cache-ephemeral`, and other lanes keep using the old PVC until each is
individually re-homed:

1. Inventory consumers of `model-cache` (glm53 v1.10 active lane,
   `dsv41-parity`, `tensorfold-glm53-v14`, old deepseek/qwen lanes).
2. For each lane worth keeping: point its `models` PVC at
   `model-cache-ephemeral` (or a new per-lane subPath), re-download its model
   via its own pull Job, validate, activate.
3. When no consumer remains: `kubectl delete pvc model-cache -n llm-test`, then
   delete the retained PV `pvc-afa2ecdd-04ae-4af9-9e08-e1ea1c6d1947` and (only
   after confirming nothing else uses the backed-up bucket) the
   `juicefs-mc`-bucket snapshot data. Backups of the old bucket can then be
   dropped from the backup schedule.
4. The old JuiceFS filesystem (`juicefs-sc` / `juicefs-mc` bucket) stays for
   anything still genuinely needing backed-up storage; only the LLM cache
   moves.

## Rollback

Keep the old lane manifests (nothing is deleted by this change). To roll back:
`desiredState: Standby` on the 1017 workload (or delete the CRD), restore the
previous lane's residency via Conductor, restore the LiteLLM route. The old
`model-cache` PVC and its data are untouched throughout.
