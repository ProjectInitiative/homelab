# GLM-5.3-Flash EXL3 — MIAI Kubernetes parity lane

- Upstream: `https://github.com/MiaAI-Lab/GLM-5.3-Flash-EXL3-2x-DGX-Sparks`
- Commit: `9348755`
- Image: `ghcr.io/miaai-lab/glm-5.3-flash-2x-dgx-sparks:exl3@sha256:eecb36e14dc34c92d46827fde7b09f7e0bf27e27c426ece126376c02dea6cd2f`
- Model: `Mia-AiLab/GLM-5.3-Flash-EXL3-TR3-4bpw` @ `25a44fdbf16862a46b7cc9921142c6c81350af2f`
- Draft: `incoai/GLM-5.3-Flash-DFlash2` (k=7) @ `dc77ff1c99eeb2df044ee3d4f0094eb033fee410`
- Served model id: `GLM-5.3-Flash-EXL3`
- Command source: `start.sh` in-container script (`write_inner_scripts`,
  `emit_overlay_block`), resolved for the 2-node / TP=2 / DFlash2 default config.

## Difference classification

| Area | Classification | Details |
|---|---|---|
| Image, overlay patches, vLLM argv, env | IDENTICAL | Resolved from the pinned `start.sh` launch (docker run env + in-container serve script) |
| Model preparation | MODEL PREP EXCEPTION | No downloader/prepare runs in the parity pod; the pinned snapshots are mounted from the shared `model-cache` PVC and fail-closed via `test -f` |
| RuntimeClass/GPU, host network/IPC, node pinning, Services, rank startup, InfiniBand | K8S PLATFORM ADAPTER | Required Kubernetes orchestration translation |
| Runtime-only patches (`patch_adaptive_k.py`, `patch_dense_fp8.py`) | K8S PLATFORM ADAPTER | Delivered via ConfigMap (the image does not bake them; `start.sh` bind-mounts them). Guarded `[ -f ]` — OFF by default |
| Boot-shape warmup | K8S PLATFORM ADAPTER (NOT WIRED) | `scripts/boot-shape-warmup.sh` post-`/health` is nonfatal and not yet added to this lane |

## Pinned profile (default `.env` resolution)

- `PORT=8888`, `TP=2`, `NNODES=2`, `MASTER_PORT=29521`
- `MAX_MODEL_LEN=850000`, `GPU_MEM_UTIL=0.85`, `MAX_NUM_SEQS=4`, `MAX_NUM_BATCHED_TOKENS=7168`
- `KV_CACHE_DTYPE=fp8`, `QUANTIZATION=exl3`, `SPEC_METHOD=dflash`, `DFLASH_TOKENS=7`, `DFLASH_DRAFT_TP=2`
- `LANGUAGE_MODEL_ONLY=0`, `SKIP_MM_PROFILING=1`, `LIMIT_MM={"image":100,"video":1}`
- `EXL3_FAT_GROUPED=1` (E3 grouped fat-expert), `EXL3_FAT_KERNEL=1`
- HF cache mounted from PVC subPath `.cache/huggingface` at `/cache/huggingface`
- CX7 backplane: `enp1s0f1np1` (`mlx5_1`, GID index 2); head `172.16.5.55`, worker `172.16.5.56`

## Resolved serve argv (head / rank 0)

```
vllm serve <MODEL_DIR>
  --served-model-name GLM-5.3-Flash-EXL3
  --host 0.0.0.0 --port 8888
  --tensor-parallel-size 2 --nnodes 2 --node-rank 0
  --master-addr 172.16.5.55 --master-port 29521
  --distributed-executor-backend mp
  --tool-call-parser glm47 --enable-auto-tool-choice --reasoning-parser glm45
  --enable-prefix-caching --no-enable-flashinfer-autotune
  --quantization exl3 --max-model-len 850000 --gpu-memory-utilization 0.85
  --max-num-seqs 4 --max-num-batched-tokens 7168 --kv-cache-dtype fp8
  --speculative-config '{"method":"dflash","model":<DFLASH_MODEL_DIR>,"num_speculative_tokens":7,
     "kv_cache_dtype":"auto","draft_sample_method":"probabilistic",
     "rejection_sample_method":"standard","draft_tensor_parallel_size":2}'
  --chat-template /opt/glm53/chat_template.jinja
  --limit-mm-per-prompt '{"image":100,"video":1}' --skip-mm-profiling
  --cudagraph-capture-sizes 1 2 4 8 16 24 32
```

Worker (rank 1) is identical except `--node-rank 1` and `--headless` immediately
after `--distributed-executor-backend mp`.

## Cache mapping

| Upstream path | Node-local backing |
|---|---|
| `/root/.cache/huggingface` | PVC `model-cache` subPath `.cache/huggingface` (mounted at `/cache/huggingface`) |
| `/root/.triton/cache` | `/var/lib/llm-test/jit-cache/triton` |
| `/root/.tilelang/cache` | `/var/lib/llm-test/jit-cache/tilelang` |
| `/root/.cache/vllm` | `/var/lib/llm-test/jit-cache/vllm-cache` |
| `/tmp` | `/var/lib/llm-test/jit-cache/glm53-tmp` |
| `/dev/shm` | emptyDir (Memory, 64 GiB) |
| `/dev/infiniband` | hostPath `/dev/infiniband` |

## Not carried over from the DeepSeek lane

- The DeepSeek lane delivered a large ConfigMap patch tree because its shared
  base image did **not** bake the Anemll hotfixes. The GLM public image **bakes**
  its overlay at build time, so only the two runtime-only patches are delivered.
- The DeepSeek worker-first `rank1-starting` / `:9090` coordination probe is not
  needed here; vLLM multi-node rendezvouses over `--master-addr` (rank 0 coordinator).

## Model download status (as of this build)

The shared JuiceFS cache contains the **NVFP4** variant
(`models--LibertAIDAI--GLM-5.3-Flash-NVFP4`, 182 G) but **not** the EXL3 weights
or the DFlash2 draft. Run `glm53-exl3-download` before scaling the lane.
