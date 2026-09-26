# TensorFold GLM-5.3-Flash lane (2x DGX-Spark)

**Status: prepared, not deployed.** The download Job starts suspended and the
serving Deployments ship with `replicas: 0`. Nothing here touches the resident
MiaAI EXL3 pair (checked-in manifests remain zero-replica; the live pair is
scaled outside Git).

This lane exists to evaluate [TensorFold](https://github.com/ashhart/TensorFold)
(`v0.3.4` = `2f8e514b0b7d615df7c971627ce3c0fb7e55d93a`, MIT, alpha) as an
alternative inference engine for GLM-5.3-Flash on the DGX Spark pair.

## What TensorFold is (and is not)

- OpenAI-compatible server (`/v1/chat/completions`, `/v1/models`, `/health`)
  on port 8080. **Requests are served one at a time** — no continuous batching.
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
  split the checkpoint per rank, rendezvous over the common Kubernetes network,
  and expose one OpenAI-compatible endpoint on port 8180 (host network).
- `services.yaml` — internal ClusterIP Service for the rank-0 API.

## Weights

| Item | Value |
|---|---|
| Engine | `ashhart/TensorFold@v0.3.4` (`2f8e514b0b7d615df7c971627ce3c0fb7e55d93a`) |
| Base image | `nvcr.io/nvidia/pytorch:26.07-py3` |
| Checkpoint | `Vontra/GLM-5.3-Flash-MLX-4bit-MTP` @ `76add2a341a1cd90ad0e86bb69839ea9c35827c6` (~169 GiB, MIT) |
| Draft | `incoai/GLM-5.3-Flash-DFlash2` (already cached; CC BY-NC-ND 4.0) |
| Served model id | `GLM-5.3-Flash-MLX` |
| API | `http://<head-node>:8180/v1` (host network) |

## Deployment order (manual, transient)

```bash
# 1. Fill the cache (Job is suspended; resume it to run)
kubectl apply --server-side -f llm-test/tensorfold-glm53/05-tensorfold-download.yaml
kubectl unsuspend job tensorfold-cache-pull -n llm-test

# 2. Create the zero-replica serving resources
kubectl apply --server-side -f llm-test/tensorfold-glm53/12-tensorfold-glm53.yaml
kubectl apply -f llm-test/tensorfold-glm53/services.yaml

# 3. Scale worker (rank 1) first, then head (rank 0)
kubectl scale deploy tensorfold-glm53-worker -n llm-test --replicas=1
kubectl wait --for=jsonpath='{.status.containerStatuses[0].started}'=true \
  pod -l app=tensorfold-glm53-worker -n llm-test --timeout=15m
kubectl scale deploy tensorfold-glm53-head -n llm-test --replicas=1
kubectl wait --for=condition=Ready pod -l app=tensorfold-glm53-head \
  -n llm-test --timeout=3600s
```

Port 8180 was chosen because 8000 (EXL3 lane) and 8888 (upstream default) are
taken by the resident pair; the exclusive host-port slot rule is preserved.

## Caveats

- Kernel compilation happens on first start (~200–230 s to ready upstream).
- TensorFold serves one request at a time; latency-sensitive concurrent agent
  traffic will queue.
- The DFlash2 drafter is non-commercial licensed; keep it out of any
  commercial serving decision.
- Both ranks must have identical settings; a draft pulled on one Spark only
  will refuse to start (`--drafter none` on both disables it).
