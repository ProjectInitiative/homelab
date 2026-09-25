# GLM-5.3-Flash EXL3 (2x DGX Spark) — MIAI parity lane

This directory is the **GLM-5.3-Flash EXL3** parity lane, mirroring the
DeepSeek lane in `../miaai-parity/`. It is a faithful Kubernetes port of the
upstream MiaAI Lab recipe
[GLM-5.3-Flash-EXL3-2x-DGX-Sparks](https://github.com/MiaAI-Lab/GLM-5.3-Flash-EXL3-2x-DGX-Sparks)
(`start.sh`) so it can run as a self-contained, deployable workload on the same
2× NVIDIA GB10 (SM121) kit the DeepSeek lane uses.

> **PRE-DEPLOY.** The Deployments here default to `replicas: 0`. Nothing is
> started by applying these files. The model weights are **not yet downloaded**;
> you must run the download job first (see below) and only then scale up.

## Files

- `05-glm53-exl3-download.yaml` — weight puller for the EXL3 model + DFlash2 draft.
- `12-glm53-assets.yaml` — ConfigMap with the reviewed runtime overlays needed
  on top of the pinned public image. It includes the bounded Mamba-state fixes,
  current scheduler/DFlash-prefix composition, and the existing EXL3/adaptive-k/
  dense-FP8 overrides, all sourced from the reviewed upstream commit.
- `12-glm53-parity.yaml` — dynamically scheduled TP2 head/worker Deployments,
  headless rendezvous Services, and node-local RoCE discovery; `replicas: 0`.
- `services.yaml` — direct in-cluster and Tailscale Services for the dynamic head.
- `13-glm53-warmup.yaml` — upstream DFlash/sampler/kpool post-ready warmup.
- `12-glm53-profile.env` — the full resolved runtime profile (documentation).
- `12-glm53-parity-diff.md` — parity comparison record.
- `../lanes/glm53/` — checksum-locked upstream comparison snapshot, local
  contract, and generated drift report. It is review evidence only and is not
  consumed by these Deployments.

## Key pins

| Item | Value |
|---|---|
| Runtime recipe baseline | `9348755653f6f8cda5d56562c05462724c40fcbd` (the last image-bound baseline in the provenance schema) |
| Last reviewed upstream HEAD | `d0b960816ba15c37927247ff74a6d04e59b00a3e` |
| Provenance contract | [`../lanes/glm53/upstream.lock.json`](../lanes/glm53/upstream.lock.json) and generated [`drift.md`](../lanes/glm53/drift.md) |
| Image (public) | `ghcr.io/miaai-lab/glm-5.3-flash-2x-dgx-sparks:exl3-instanttensor` |
| Image digest | `sha256:447114ee77d14c9b4732ee23978ada2a0ee9027868a231d6fd42700a8b25be1d` |
| Runtime adoption status | **SOURCE-OVERLAY UPDATE** — the public image digest is unchanged, while reviewed Python overlays from `d0b9608` are mounted explicitly; native thin-decode remains disabled because it requires a matched image build |
| Weight model | `Mia-AiLab/GLM-5.3-Flash-EXL3-TR3-4bpw` @ `25a44fdbf16862a46b7cc9921142c6c81350af2f` (~164 GiB, 120 shards) |
| Draft model | `incoai/GLM-5.3-Flash-DFlash2` (k=7) @ `dc77ff1c99eeb2df044ee3d4f0094eb033fee410` (~2.3 GiB) |
| Served model id | `GLM-5.3-Flash-EXL3` |
| API port | **8000** (GLM) vs 8000 (DeepSeek) |
| KV cache dtype | `fp8` (fp8_ds_mla) |
| Quantization | `exl3` |

## Step 1 — download the weights (required)

The previous `llm-test/20-glm.yaml` puller fetches
`LibertAIDAI/GLM-5.3-Flash-NVFP4`, which is a **different (NVFP4/Ray) variant** and
is NOT what this EXL3 lane serves. The cache-preload Job is `glm53-cache-pull`; do not scale the lane unless its
completion is confirmed and the pinned EXL3 and DFlash2 snapshot files pass the
init-container checks. A missing stale NVFP4 directory is a successful delete
no-op.

```bash
kubectl apply -f llm-test/glm53-parity/05-glm53-exl3-download.yaml
kubectl wait --for=condition=Complete job/glm53-cache-pull -n llm-test --timeout=1h
```

Verify on the shared volume (RWX JuiceFS, reachable on the nodes):

```bash
ssh chronometer 'ls /var/lib/juicefs/volume/pvc-afa2ecdd-04ae-4af9-9e08-e1ea1c6d1947-fwcslx/.cache/huggingface/ | grep -i glm53'
```

You should see `models--Mia-AiLab--GLM-5.3-Flash-EXL3-TR3-4bpw` and
`models--incoai--GLM-5.3-Flash-DFlash2`.

## Step 2 — stop the resident pair and install resources

Because the checked-in Deployments intentionally declare `replicas: 0`, applying
this manifest to a live pair stops it. Shut down in rank order first, and wait for
host port/GPU release. ConfigMap `subPath` mounts update only on pod recreation.

```bash
kubectl scale deploy glm53-exl3-head -n llm-test --replicas=0
kubectl wait --for=delete pod -l app=glm53-exl3-head -n llm-test --timeout=10m
kubectl scale deploy glm53-exl3-worker -n llm-test --replicas=0
kubectl wait --for=delete pod -l app=glm53-exl3-worker -n llm-test --timeout=10m
kubectl apply --server-side -f llm-test/glm53-parity/12-glm53-assets.yaml
kubectl apply --server-side -f llm-test/glm53-parity/13-glm53-warmup.yaml
kubectl apply --server-side -f llm-test/glm53-parity/12-glm53-parity.yaml
```

## Step 3 — scale up (worker rank 1 first, then head rank 0)

Start the headless worker and confirm its container is running before starting the
coordinator/API. Do not rely on a fixed sleep. The head remains Kubernetes-unready
until the API is healthy and the upstream boot-shape warmup completes.

```bash
kubectl scale deploy glm53-exl3-worker -n llm-test --replicas=1
kubectl wait --for=jsonpath='{.status.containerStatuses[0].started}'=true \
  pod -l app=glm53-exl3-worker -n llm-test --timeout=10m
kubectl scale deploy glm53-exl3-head -n llm-test --replicas=1
kubectl wait --for=condition=Ready pod -l app=glm53-exl3-head -n llm-test --timeout=3600s
```

## Step 4 — expose (optional, only once running)

```bash
kubectl apply --server-side -f llm-test/glm53-parity/services.yaml
```

Endpoint: `http://glm.taildeab2.ts.net/`. Both the Tailscale LoadBalancer and
LiteLLM target the stable `glm53-head` Service directly, while the vLLM API
listens on whichever Spark hosts the head pod at `0.0.0.0:8000`.

## Verify

```bash
kubectl get pods,deploy,svc -n llm-test -o wide | grep glm53
kubectl logs -n llm-test deploy/glm53-exl3-head -c vllm --tail=100
kubectl logs -n llm-test deploy/glm53-exl3-worker -c vllm --tail=100
curl -i http://glm53-head.llm-test.svc.cluster.local:8000/health   # inside cluster DNS
curl http://glm.taildeab2.ts.net/v1/models
```

## Notes / caveats

- The reviewed upstream HEAD is **not** represented by a newer public image;
  GHCR still resolves to the pinned digest. The current pure-Python overlays are
  therefore mounted explicitly on both ranks. They include the Mamba chunk
  alignment and superseded-state release fixes that bound memory during long
  asynchronous prefills. Native `GLM53_EXL3_MOE_FAST` remains disabled because
  it requires a provenance-matched native image rebuild.
  `GLM53_KDA_BF16_LARGE_M=0` intentionally releases roughly 3.29 GiB/rank versus
  the prior staged profile. `GLM53_DRAFT_KV_COMPACT=0` remains conservative: the
  opt-in reduces allocator IDs but does not reduce backing VRAM. Multimodal caps
  and local 512k/16/2048/0.88/15-GiB geometry are used.
- The public image contains an older baked recipe (`glm53.recipe.stamp`), while
  `glm53-parity-overlay` supplies the reviewed source-only updates. The runtime
  applies them in upstream `GLM53_OVERLAY_ORDER`; installers are versioned,
  idempotent, and fail closed on unsupported source drift. Reconcile or remove
  these mounts when a provenance-matched image is eventually published.
- Boot-shape warmup is mounted from `13-glm53-warmup.yaml`, starts automatically
  after `/health`, and gates the head pod's Kubernetes readiness. JIT warnings
  emitted while this sweep runs are expected; successful readiness means its
  DFlash, rejection-sampler, and kpool-tail shape requests completed.
- The API key is read by vLLM natively via `VLLM_API_KEY` (never argv). Set it in
  the Deployment env or a Secret before scaling; empty = unauthenticated.
- The serving profile is `MAX_MODEL_LEN=512000` with `GPU_MEM_UTIL=0.88` and an
  explicit 15 GiB KV cap. This trades some GB10 unified-memory headroom for
  additional concurrent long-context capacity. DFlash2 remains TP-sharded with
  `DFLASH_DRAFT_TP=2`.
- The scheduler uses the upstream-tested high-concurrency geometry:
  `MAX_NUM_SEQS=16` with `MAX_NUM_BATCHED_TOKENS=2048`. Sixteen is an admission
  ceiling, not a reservation; paged/grouped KV allocation and the 15 GiB pool
  determine how many active histories fit at runtime.
- `GLM53_MIXED_PREFILL_CHUNK=off` preserves normal vLLM continuous batching:
  newly arriving agent prefills may share engine steps with active decodes. The
  upstream `skip` policy protects one stream's decode latency but can make other
  agents appear stalled while their prompts remain deferred.
- `EXTRA_ARGS` ships the default DFlash2 CUDA-graph capture list
  `--cudagraph-capture-sizes 1 2 3 4 5 8 16 24 32`. The adaptive-k / FP8-dense
  fast paths need a longer list and a KV cap; see the upstream `.env.example`.
- Scheduling and networking are capability-based: `runtimeClassName:
  nvidia-rdma` contributes the Spark/GPU/arm64/RoCE/topology node selectors,
  while required hostname anti-affinity places the two ranks on distinct
  eligible nodes. Each rank requests one GPU and one
  `rdma/hca_shared_devices` allocation. The plugin's single shared allocation
  injects all four matched HCA device sets; this was verified in unprivileged
  pods on all three Sparks. Headless-Service DNS and the common `172.16.4.x`
  network carry rendezvous; `/var/lib/dgx-spark/rdma-fabric.json` plus sysfs
  select the two RoCE rails and matching GID for the actual node pair. No
  serving manifest contains a node hostname, direct-link IP, Linux netdev, or
  `mlx5_N` identifier.

## Continuous-batching load test

`test-continuous-batching.py` starts a long anchor decode, waits for its first
output token, then injects multiple unique large prompts. Its live table shows
scheduler occupancy, queue reasons, KV usage, and prompt/generation progress in
the same metrics interval. Its final report includes per-request effective prefill,
decode, and delivered generation rates plus aggregate prompt/completion totals.

```bash
python3 llm-test/glm53-parity/test-continuous-batching.py \
  --load-requests 2 \
  --prompt-tokens 30000 \
  --anchor-output-tokens 1200 \
  --load-output-tokens 200 \
  --output /tmp/glm53-continuous-batching.json
```

Interpretation:

- `prompt_delta > 0` and `gen_delta > 0` in one row proves mixed prefill/decode
  progress.
- `defer > 0` means a policy blocked otherwise schedulable work; with
  `GLM53_MIXED_PREFILL_CHUNK=off`, this should remain zero.
- `wait`/`cap > 0` can still occur when sequence, token-budget, or KV capacity is
  exhausted; continuous batching does not imply unlimited admission.
- Prometheus counters include all endpoint traffic, so run the test while other
  clients are idle for an isolated measurement.

For a throughput-oriented test, `benchmark-concurrent-prompts.py` releases
three or four complex coding requests from a barrier at the same instant. It
reports each stream's effective prefill, TTFT, decode-only throughput, delivered
throughput, total duration, and token counts, followed by shared-wall-clock
aggregate totals:

```bash
python3 llm-test/glm53-parity/benchmark-concurrent-prompts.py \
  --requests 4 \
  --prompt-tokens 30000 \
  --max-tokens 600 \
  --output /tmp/glm53-concurrent-prompts.json
```

Pass `--thinking` to model reasoning-heavy agent traffic. Use `--prompts-json`
with a JSON array of task strings to benchmark actual project prompts. Summed
per-stream rates are diagnostic only; the shared-window aggregate fields are
the hardware-throughput measurements.

Both scripts read an optional bearer token from `OPENAI_API_KEY` or
`VLLM_API_KEY`; neither accepts secrets as command-line arguments.
