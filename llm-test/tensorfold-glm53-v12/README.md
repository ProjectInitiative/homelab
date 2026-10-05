# TensorFold GLM-5.3-Flash v1.2 recipe lane (2x DGX-Spark) — ACTIVE

**Status: SERVING.** The live Deployments are scaled to one rank each; the
checked-in replica counts remain zero so activation stays explicit. LiteLLM's
`dgx-spark` alias routes to `tensorfold-v12-head:8000`. Direct tests from the
`ai-proxy` pod and an end-to-end request through `ai.taildeab2.ts.net` passed.

Activation requires a privileged final init step on each Spark to run
`sync; echo 3 > /proc/sys/vm/drop_caches` and require at least 110 GiB
`MemAvailable`. These nodes retain VM cache after a large model exits; without
that gate TensorFold's startup budget can incorrectly estimate a zero-token
window. All init containers also force
`NVIDIA_DRIVER_CAPABILITIES=compute,utility` because the image default includes
the unsupported `video` capability.

Both ranks use the cluster-scoped `llm-serving-critical` PriorityClass at
`999999998`: the highest non-system application priority in this cluster. It
preempts ordinary workloads and is preferred during node-pressure eviction,
while Kubernetes/CSI/device-plugin and kubevirt cluster-critical storage/runtime
pods remain above it. This reduces disruption risk but cannot make a rank
survive host OOM or `NodeNotReady`; either rank loss still requires coordinated
pair recreation.

This lane is the Kubernetes port of the MiaAI Lab recipe
[GLM-5.3-Flash-EXL3-2x-DGX-Sparks-TensorFold](https://github.com/MiaAI-Lab/GLM-5.3-Flash-EXL3-2x-DGX-Sparks-TensorFold)
@ `1f3d909b00b7be7aa8f00d3a33e0b9e7aa56d221` (v1.2, 2026-10-01): TensorFold
v0.5.0 with 53 baked patches, a bigger shared KV pool (~2.1–2.9M tokens), a
1,048,576-token window, 4 concurrent streams, DFlash2 + copy drafts, 4-bit
dense weights, FP8 KV cache, vision, and the RoCE one-shot all-gather.

It runs alongside (not with) the qualified EXL3 vLLM lane
`../glm53-parity/`: the two lanes share the same GPUs and exclusive host
networks and must never scale up together.

## Why the shared model cache needs almost nothing

| Asset | Recipe v1.2 pin | Cached snapshot | Verdict |
|---|---|---|---|
| Checkpoint | `Mia-AiLab/GLM-5.3-Flash-EXL3-TR3-4bpw @ 9eaebb7c…` | `@ 25a44fdb…` | **byte-identical** (all 120 shards + config/tokenizer/index share LFS sha256 oids; only README.md differs) → serve the cached snapshot, no re-download |
| Drafter | `incoai/GLM-5.3-Flash-DFlash2 @ bf582e4e…` | `@ dc77ff1c…` | **model.safetensors differs** → pull the new ~2.34 GiB snapshot with the cache-align Job |

The checkpoint verification is baked into the init container
(`verify-checkpoint.py`): 120/120 shards, exact byte total
(175,642,157,752), index weight-map coverage, and the DFlash2 v1.2 snapshot
size (2,342,169,800). The lane fails fast at init if the cache drifts.

## Files

- `05-dflash2-v12-cache-align.yaml` — one-shot cache-pull Job (puller v3) for
  DFlash2 @ `bf582e4e…`. Run once before activation. Deleting nothing: the
  `dc77ff1c` draft stays as EXL3-lane rollback material.
- `12-tensorfold-v12-glm53.yaml` — the two-rank Deployments (`replicas: 0`),
  headless rendezvous Services (master port 29551), RoCE-fabric discovery
  ConfigMap, launch scripts, and the head's rank-1 start gate.
- `services.yaml` — internal ClusterIP Service for the rank-0 API (port 8000).

## Key pins

| Item | Value |
|---|---|
| Upstream recipe | `MiaAI-Lab/GLM-5.3-Flash-EXL3-2x-DGX-Sparks-TensorFold @ 1f3d909` (v1.2) |
| Engine | TensorFold `v0.5.0`, 53 patches, baked into the published image (`tf.patches=cb7c56f7f921`) |
| Image | `ghcr.io/miaai-lab/glm-5.3-flash-exl3-2x-dgx-sparks-tensorfold@sha256:6ee3c6e0430040b69ddcb0c96c7fbbcb94a5bed47d48a8ba092626369ae533b9` (verified arm64 linux, 11.4 GiB) |
| Checkpoint served | `Mia-AiLab/GLM-5.3-Flash-EXL3-TR3-4bpw` cached snapshot `25a44fdb…` (byte-identical to the recipe pin `9eaebb7c…`) |
| Drafter served | `incoai/GLM-5.3-Flash-DFlash2` @ `bf582e4e…` (v1.2 pin, cache-aligned) |
| Served model id | `GLM-5.3-Flash-EXL3` |
| API | `http://<head-node>:8000/v1` (host network; the mutually exclusive TP2 lanes reuse the established inter-node port) |
| Rendezvous | headless Services, master port 29551, control network 172.16.4.x |
| KV profile | `TENSORFOLD_MEMORY_RESERVE_GIB=14.5`, `TF_GLM_CACHE_GIB=12.5`, KV `fp8` → ~2.1–2.9M shared tokens; window 1,048,576; `--parallel 4` |
| Dense weights | `q4` (recipe default), RoCE comm with `TF_ROCE_MAX_KB=512` |

Runtime env carries the recipe's `TF_GLM_*` / `TF_ROCE_*` defaults verbatim
(config.sh v1.2): copy drafts + max 15, `fnc7:0.3` draft policy, HC split +
prefill overlap, chunked KDA, wide code graphs (16), multi-prefill, L2
prefetch, `nc` EXL3 loads, shared-prefix reuse. `VISION=1`, `THINKING=1`,
`VISION_URLS=0` (data URLs only).

## Staging (what was done / idempotent re-stage)

```bash
kubectl apply --server-side -f llm-test/tensorfold-glm53-v12/12-tensorfold-v12-glm53.yaml
kubectl apply -f llm-test/tensorfold-glm53-v12/services.yaml
kubectl get deploy -n llm-test | grep tensorfold-v12   # both at 0/0
```

Nothing runs after staging: no GPU, no host port, no memory is claimed.
The lane is capability-scheduled (`nvidia-rdma`, hostname anti-affinity), so it
can land on any two eligible Sparks at activation time.

## Step 1 — align the drafter snapshot (once, before activation)

```bash
kubectl apply -f llm-test/tensorfold-glm53-v12/05-dflash2-v12-cache-align.yaml
kubectl wait --for=condition=Complete job/dflash2-v12-cache-align -n llm-test --timeout=1h
```

~2.34 GiB at the site-link cap. If this Job has not completed, the lane's init
containers fail fast with "drafter snapshot missing".

## Step 2 — exclusive swap: stop the resident EXL3 pair

This lane and `glm53-exl3-*` share the same GPUs and host networks. Stop the
resident pair head-first, then worker, and wait for release:

```bash
kubectl scale deploy glm53-exl3-head -n llm-test --replicas=0
kubectl wait --for=delete pod -l app=glm53-exl3-head -n llm-test --timeout=10m
kubectl scale deploy glm53-exl3-worker -n llm-test --replicas=0
kubectl wait --for=delete pod -l app=glm53-exl3-worker -n llm-test --timeout=10m
```

## Step 3 — scale up: worker rank 1 first, then head rank 0

The head's init gate (`wait-for-rank1-start`) blocks rank 0 until rank 1 has
resolved its peer and selected RoCE rails ("rank 1 launching" log marker), so
rank order is enforced even if both are scaled in one motion.

```bash
kubectl scale deploy tensorfold-v12-worker -n llm-test --replicas=1
kubectl scale deploy tensorfold-v12-head -n llm-test --replicas=1
kubectl wait --for=condition=Ready pod -l app=tensorfold-v12-worker -n llm-test --timeout=15m
kubectl wait --for=condition=Ready pod -l app=tensorfold-v12-head -n llm-test --timeout=3600s
```

Notes:

- First start compiles the GB10 CUDA kernels once (a few minutes); they are
  cached per node under `/var/lib/llm-test/tensorfold-v12-kernel-cache`.
- Loading ~80 GiB of weights takes 2–6 minutes per start.
- The recipe wants ~110 GiB free memory per Spark at start; the init
  container drops the host page cache first, exactly like the EXL3 lane's
  preflight. Stop other GPU/memory work on the pair before scaling up.
- Upstream boots rank 1 first for the same reason: either rank ending takes
  the other down (they wait for their peer forever otherwise).

## Step 4 — verify

```bash
kubectl logs -n llm-test deploy/tensorfold-v12-head -c tensorfold --tail=50
curl -s http://<head-node-ip>:8000/v1/models
curl -s http://tensorfold-v12-head.llm-test.svc.cluster.local:8000/v1/models   # in-cluster
curl -s http://<head-node-ip>:8000/v1/chat/completions -H 'Content-Type: application/json' \
  -d '{"model":"GLM-5.3-Flash-EXL3","messages":[{"role":"user","content":"Say OK."}],"max_tokens":2000}'
```

The model thinks before answering (`reasoning_content`); give replies enough
`max_tokens`. Baked image runs TensorFold v0.5.0 with the full 53-patch set —
no pip installs, no patch mounts at pod start (the v0.3.4 lane's
install-at-start pattern is retired with that lane).

## Step 5 — LiteLLM cutover (only once healthy)

Mirror `../glm53-parity/services.yaml`: point a Service/alias at
`tensorfold-v12-head.llm-test.svc.cluster.local:8000` with model id
`GLM-5.3-Flash-EXL3`, then restart `ai-proxy`. The primary client endpoint
remains `http://ai.taildeab2.ts.net/`.

## Rollback to the EXL3 lane

Stop this lane head-first, then worker; start the EXL3 worker before its head;
restore the `dgx-spark` route in `llm-test/miaai-parity/services.yaml` to
`glm53-head` and restart `ai-proxy`:

```bash
kubectl scale deploy tensorfold-v12-head -n llm-test --replicas=0
kubectl wait --for=delete pod -l app=tensorfold-v12-head -n llm-test --timeout=10m
kubectl scale deploy tensorfold-v12-worker -n llm-test --replicas=0
kubectl wait --for=delete pod -l app=tensorfold-v12-worker -n llm-test --timeout=10m
kubectl scale deploy glm53-exl3-worker -n llm-test --replicas=1
kubectl scale deploy glm53-exl3-head -n llm-test --replicas=1
```

## Activation receipt (2026-10-01)

- The first attempt exposed two deployment requirements: override the image's
  unsupported `video` driver capability, and reclaim the Sparks' known retained
  VM cache immediately before each TensorFold process starts.
- A dedicated final `reclaim-vm-cache` init now retries cache reclamation for a
  bounded minute and fails closed below 110 GiB `MemAvailable`. The successful
  run passed on the first attempt at ~116 GiB on both ranks.
- Both ranks discovered the peer dynamically, selected both CX7 rails
  (`mlx5_0` + `mlx5_2`, GID 3), and allocated the native 1,048,576-token window.
  Rank 0 estimated 88.09 GiB within a 100.37 GiB budget; rank 1 estimated
  86.29 GiB within 100.34 GiB.
- The engine loaded successfully with a ~2.89M-token shared pool, DFlash2,
  vision, four streams, and the full 1M per-request context.
- Port 8880 was healthy only on head-node localhost but timed out from
  `ai-proxy`. The mutually exclusive DGX lanes now consistently reuse the
  established host/API and Service port 8000 (keel DEC-0023).
- From the actual `ai-proxy` pod, `/health`, `/v1/models`, and a direct
  completion passed. After LiteLLM cutover, the public `dgx-spark` alias returned
  `LITELLM_TENSORFOLD_OK` in 1.05 seconds.

## Known risks / honest caveats

- **Engine history.** The earlier TensorFold v0.3.4 experiment
  (`../tensorfold-glm53/`) proved NCCL TP2 setup on this fabric but never
  served long context. v0.5.0 with the recipe's memory budgeting
  (`TENSORFOLD_MEMORY_RESERVE_GIB`) is a different engine generation and the
  upstream-measured config, but treat the first boot as unproven here.
- **RoCE transport.** Patch 0006's one-shot all-gather negotiates between the
  ranks through NCCL and falls back to NCCL if geometry mismatches
  (`TF_GLM_COMM=roce`); the fabric ConfigMap exports the same HCA/GID env the
  patch reads. A RoCE setup failure surfaces in rank 0's log, not silent
  slowdown.
- **Memory envelope.** Rank 0 estimated ~88 GiB at a 1M window + the capped
  12.5 GiB pool; the 128 GiB pod limit mirrors the EXL3 lane. If the head
  refuses the window, the recipe's documented behavior is a named fallback —
  capture it from the log rather than guessing a smaller `--context`.
- **DFlash2 license.** CC BY-NC-ND 4.0: non-commercial serving only.
- **LiteLLM.** The `ai` front door still routes to the EXL3 lane until step 5.

## Provenance

- Recipe fetched and reviewed at `1f3d909b00b7be7aa8f00d3a33e0b9e7aa56d221`
  (`scripts/config.sh`, `start.sh`, `scripts/nodes.sh`,
  `patches/0006-cuda-roce-allgather.patch`).
- HF tree API used to prove checkpoint byte-identity across pins (LFS oids,
  2026-02-13) and to size the DFlash2 delta pull.
- GHCR digest resolved and inspected (arm64, patches label) before staging.
