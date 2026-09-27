# TensorFold GLM-5.3-Flash lane (2x DGX-Spark)

**Status: TensorFold is not deployed; the qualified EXL3 service is restored.**
The pinned snapshot has all 43 shards (181,709,451,790 bytes). The Sep 27
experiment proved TP2 NCCL setup and a short direct/LiteLLM completion, but the
live command had no `--context` override and therefore served only the CUDA
engine's 2,051-token dense limit. Pi's 25,242-token prompt plus 16,384 requested
output tokens was rejected. EXL3 is Ready and LiteLLM `dgx-spark` points back to
it. TensorFold Deployments are at zero until a memory-feasible long-context
implementation is available; see the context analysis below. The earlier
NCCL refusal at `172.16.4.56:37351` remains unexplained.

The Spark direct-link topology spans pair-specific `.5`–`.10` subnets. The
Kubernetes RDMA shared-device resource/runtime class handle allocation and
eligible placement; headless Services provide dynamic peer discovery; the
node-local inventory maps the selected peer to its correct links. `.4` is the
10Gb Kubernetes/control network, not the NCCL bulk-data path. No subnet, node,
netdev, or HCA identifier is hardcoded in the workload.

This lane exists to evaluate [TensorFold](https://github.com/ashhart/TensorFold)
(`v0.3.4` = `2f8e514b0b7d615df7c971627ce3c0fb7e55d93a`, MIT, alpha) as an
alternative inference engine for GLM-5.3-Flash on the DGX Spark pair.

## What TensorFold is (and is not)

- OpenAI-compatible server (`/v1/chat/completions`, `/v1/models`, `/health`)
  on port 8000 in this lane. **Requests are served one at a time** — no continuous batching.
- Exact speculative decoding: drafted replies are byte-identical to serial
  decoding (`"draft": false` gives the serial reference).
- Claims 1.5–2.1x single-stream decode vs the MiaAI vLLM recipe on 2x GB10.
  Self-reported, unaudited; depends heavily on draft acceptance.
- **Reads MLX affine 4-bit checkpoints only for GLM** (groups of 64, plus the
  Mia-AiLab EXL3 TR3-4bpw as an experiment). It **refuses NVFP4, GPTQ, AWQ**.
- `--tp 2 --rank R --master HOST`: exactly two ranks, one per Spark, over the
  direct 200 Gb/s link. Rank 1 starts first; rank 0 serves HTTP.
- Young single-author project (2026-06), WIP release, GB10 page-migration
  stalls documented upstream, no concurrent-request throughput story.

## Why not NVFP4

The requested "non-MiaLabs GLM-5.3 flash" NVFP4 variant
(`RedHatAI/GLM-5.3-Flash-NVFP4`) is **not consumable by TensorFold**: the engine
refuses NVFP4 before anything downloads. The checkpoint TensorFold actually
tests GLM with is `Vontra/GLM-5.3-Flash-MLX-4bit-MTP` (MLX 4-bit with MTP head,
~169 GiB across 43 shards, MIT). The cache already holds `RedHatAI/GLM-5.3-Flash-NVFP4`
and `drowzeys/keys-GLM-5.3-Flash-NVFP4-ablit-l15-45-anchorstock`, so NVFP4
remains available for future vLLM-side work without new downloads.

## Files

- `05-tensorfold-download.yaml` — cache puller Job (suspended). Pulls
  `Vontra/GLM-5.3-Flash-MLX-4bit-MTP@76add2a3…`. The DFlash2 draft
  (`incoai/GLM-5.3-Flash-DFlash2`, CC BY-NC-ND 4.0) is already cached from the
  EXL3 lane, so no re-download is needed.
- `12-tensorfold-glm53.yaml` — two-rank Deployments (`replicas: 0`) that
  install TensorFold inside `nvcr.io/nvidia/pytorch:26.07-py3` at pod start,
  rendezvous over common-network DNS, and select peer RoCE HCAs/GID from each
  node's fabric inventory. Both ranks read the shared snapshot directly; this
  avoids writing a ~91-GiB split to ephemeral storage (at the cost of ~1/3 more
  checkpoint reads than upstream's optional per-rank split). Init verifies all
  43 shards; the head init gate waits for rank 1's peer/fabric setup log marker
  before rank 0 launches. Containers set `NVIDIA_DRIVER_CAPABILITIES` to the
  runtime-supported `compute,utility`.
  The API uses 8000.
- `services.yaml` — internal ClusterIP Service for the rank-0 API.

## Weights

| Item | Value |
|---|---|
| Engine | `ashhart/TensorFold@v0.3.4` (`2f8e514b0b7d615df7c971627ce3c0fb7e55d93a`) |
| Base image | `nvcr.io/nvidia/pytorch:26.07-py3` |
| Checkpoint | `Vontra/GLM-5.3-Flash-MLX-4bit-MTP` @ `76add2a341a1cd90ad0e86bb69839ea9c35827c6` (~169 GiB, MIT) |
| Draft | `incoai/GLM-5.3-Flash-DFlash2` (already cached; CC BY-NC-ND 4.0) |
| Served model id | `76add2a341a1cd90ad0e86bb69839ea9c35827c6` (LiteLLM alias: `dgx-spark`) |
| API | `http://<head-node>:8000/v1` (host network) |

## Deployment order (manual, transient)

```bash
# 1. Fill the cache (Job is suspended; resume it to run)
kubectl apply --server-side -f llm-test/tensorfold-glm53/05-tensorfold-download.yaml
kubectl patch job tensorfold-cache-pull -n llm-test --type merge \\
  -p '{"spec":{"suspend":false}}'

# 2. This is an exclusive 2-GPU swap; it cannot coexist with the resident MiaAI TP2.
# Stop the old head first, then worker, and wait for the GPUs to be released.
kubectl scale deploy glm53-exl3-head -n llm-test --replicas=0
kubectl wait --for=delete pod -l app=glm53-exl3-head -n llm-test --timeout=10m
kubectl scale deploy glm53-exl3-worker -n llm-test --replicas=0
kubectl wait --for=delete pod -l app=glm53-exl3-worker -n llm-test --timeout=10m

# 3. Create the zero-replica serving resources
kubectl apply --server-side -f llm-test/tensorfold-glm53/12-tensorfold-glm53.yaml
kubectl apply -f llm-test/tensorfold-glm53/services.yaml

# 4. For an explicitly approved experiment only: start rank 1, then rank 0.
#    Never scale both serving pairs up together. Rank-1 Kubernetes Ready is
#    not the same as TensorFold/NCCL readiness.
kubectl scale deploy tensorfold-glm53-worker -n llm-test --replicas=1
kubectl scale deploy tensorfold-glm53-head -n llm-test --replicas=1
kubectl wait --for=condition=Ready deployment/tensorfold-glm53-worker \
  -n llm-test --timeout=15m
kubectl wait --for=condition=Available deployment/tensorfold-glm53-head \
  -n llm-test --timeout=3600s
```

The TensorFold and MiaAI pairs both use the exclusive Spark host port 8000 and
the same two GPUs. They must not run concurrently. Host port 8000 is already
scoped to Kubernetes source CIDRs; client access is via the internal ClusterIP
Service. Returning to MiaAI requires stopping TensorFold head then worker,
starting the MiaAI worker before its head, then restoring the `dgx-spark` route
in `llm-test/miaai-parity/services.yaml` to `glm53-head` / the EXL3 model and
restarting `ai-proxy`.

## Caveats

- **Context limit:** TensorFold v0.3.4's CLI has `--context`, but the deployed
  launch scripts omitted it. For this checkpoint `index_topk=2048`, `kpool=4`,
  so the CUDA engine's default `dense_limit` is 2,051. The reported 41,626 is
  the request total (25,242 prompt + 16,384 `max_tokens`), not a measured cache
  limit. The checkpoint's `text_config.max_position_embeddings` is 1,048,576;
  that native position limit is not the same as a feasible serving context.
- **512K does not fit this TensorFold cache implementation on one Spark.** The
  installed CUDA `State` allocates about 400,128 bytes per context token per
  rank (DSA K/V and index caches, including MTP). `--context 524288` therefore
  needs about 195.4 GiB per rank for those arrays alone, before model weights,
  scratch buffers, or runtime workspace. Each Spark exposes 121.63 GiB total;
  the pod limit is 118 GiB. Do not add `--context 524288` as a superficial
  setting: it will OOM during startup. A cache/offload redesign or larger-memory
  hardware is needed before 512K is viable here.
- **NCCL history:** the first attempt's rank 1 got `Connection refused` at
  `172.16.4.56:37351` after 35 retries. In the Sep 27 retry, both ranks
  initialized NCCL; INFO showed QPs on both peer HCAs/GID 3, and rank 1 reached
  ready in 1611.3s. The head served. Short direct and LiteLLM completions passed;
  the original refusal's cause remains unknown. This is separate from the
  context/memory limit.
- Dynamic networking: the topology uses pair-specific `.5`–`.10` RoCE
  subnets. `nvidia-rdma` and `rdma/hca_shared_devices` let Kubernetes schedule
  and allocate eligible devices; headless Service DNS finds the other rank;
  node-local inventory selects that peer's links. The tested sextant–octant
  pair used `.9`/`.10`. `.4` is control/bootstrap, not the NCCL data path.
- The live candidate previously inherited a stale port-9201 worker probe; it
  and the stale Service port were removed. `NCCL_DEBUG=INFO` with `INIT,NET`
  is enabled for diagnostics. The separate GPU capability mismatch was fixed
  with `NVIDIA_DRIVER_CAPABILITIES=compute,utility`.
- Kernel compilation happens on first start (~200–230 s to ready upstream).
- TensorFold serves one request at a time; latency-sensitive concurrent agent
  traffic will queue.
- The DFlash2 drafter is non-commercial licensed; keep it out of any
  commercial serving decision.
- Both ranks must have identical settings; a draft pulled on one Spark only
  will refuse to start (`--drafter none` on both disables it).
