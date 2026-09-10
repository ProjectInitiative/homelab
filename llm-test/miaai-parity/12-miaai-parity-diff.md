# MiaAI Kubernetes parity lane

- Commit: `957890ac5e26ce149646719298169f80603a3e1f`
- Image: `ghcr.io/anemll/dspark-vllm-gx10:0.1.1@sha256:a83948492cf13df455170fb42885f5ef4db54fefe0feff0f841ecbff464ac9d8`
- Manifest: `llm-test/miaai-parity/12-deepseek-miaai-parity.yaml`
- Compose command source SHA256: `6e7c69a1efebf6e9ab0c9801e15e4c453cf63a1355a8b18ce9c3b4ab9d024bc2`

## Difference classification

| Area | Classification | Details |
|---|---|---|
| Image, command body, default hotfix gates, vLLM argv | IDENTICAL | Generated from pinned `docker-compose.dspark.yml` command scalar |
| Model preparation | MODEL PREP EXCEPTION | Existing pinned snapshot is mounted; no downloader/prepare script runs |
| RuntimeClass/GPU, host network/IPC, node pinning, Services, rank startup, InfiniBand | K8S PLATFORM ADAPTER | Required Kubernetes orchestration translation |
| libcuda discovery | K8S PLATFORM ADAPTER | Real `/usr/lib/aarch64-linux-gnu/libcuda.so.1` exposed through `/run/triton-cuda-driver` |
| Patch delivery | K8S PLATFORM ADAPTER | Complete pinned `patches/` tree delivered via ConfigMaps and staged without editing files |

## Pinned profile

- `GPU_MEMORY_UTILIZATION=0.835`
- `MAX_MODEL_LEN=1048576`
- `MAX_NUM_SEQS=6`
- `MAX_NUM_BATCHED_TOKENS=8192`
- `LONG_PREFILL_TOKEN_THRESHOLD=1024`
- `MTP_NUM_TOKENS=6`
- `DSPARK_REVISION=86f746b36186f0e567729a5c06a8c918caba82a9`
- HF cache mounted at `/cache/huggingface` from PVC subPath `.cache/huggingface`

## Complete pinned patch assets

- `patches/dsv4_tp_pad.py` — mounted in parity runtime
- `patches/fix-nvfp4-ds-mla-long-context.patch` — mounted in parity runtime
- `patches/hotfix-deepgemm-sm121-mqa-header-alias.sh` — mounted in parity runtime
- `patches/hotfix-dsv4-adaptive-prefill-chunk.py` — mounted in parity runtime
- `patches/hotfix-dsv4-assistant-final-continuation.py` — mounted in parity runtime
- `patches/hotfix-dsv4-dense-prefill-indexer-48407.sh` — mounted in parity runtime
- `patches/hotfix-dsv4-flashmla-workspace-50298.sh` — mounted in parity runtime
- `patches/hotfix-dsv4-grammar-advance.sh` — mounted in parity runtime
- `patches/hotfix-dsv4-issue133-triton-specialization.py` — mounted in parity runtime
- `patches/hotfix-dsv4-issue141-sparse-mla-decode-chunk.py` — mounted in parity runtime
- `patches/hotfix-dsv4-issue144-effort-align.py` — mounted in parity runtime
- `patches/hotfix-dsv4-issue26-hybrid-swa-min.py` — mounted in parity runtime
- `patches/hotfix-dsv4-issue27-partial-prefill-concurrency.py` — mounted in parity runtime
- `patches/hotfix-dsv4-issue31-v2-thinking-budget-gpu.py` — mounted in parity runtime
- `patches/hotfix-dsv4-issue43-decode-fairness-and-diag.py` — mounted in parity runtime
- `patches/hotfix-dsv4-issue55-tool-truncation.py` — mounted in parity runtime
- `patches/hotfix-dsv4-mtp-buffer-50312.sh` — mounted in parity runtime
- `patches/hotfix-dsv4-replicate-markov-head.py` — mounted in parity runtime
- `patches/hotfix-dsv4-responses-store.py` — mounted in parity runtime
- `patches/hotfix-dsv4-skip-empty-c128-48957.sh` — mounted in parity runtime
- `patches/hotfix-dsv4-skip-topk-49486.sh` — mounted in parity runtime
- `patches/hotfix-dsv4-sp-indexer-prefill.py` — mounted in parity runtime
- `patches/hotfix-dsv4-suppress-stops-in-reasoning.py` — mounted in parity runtime
- `patches/hotfix-dsv4-vision-exp.py` — mounted in parity runtime
- `patches/hotfix-encoding-dsv4-issue21.py` — mounted in parity runtime
- `patches/hotfix-gb10-spin-wait.sh` — mounted in parity runtime
- `patches/hotfix-nvfp4-ds-mla-issue22.sh` — mounted in parity runtime
- `patches/hotfix-vllm-c128a-prefill-cache.py` — mounted in parity runtime
- `patches/hotfix-vllm-codex-agent-message.py` — mounted in parity runtime
- `patches/hotfix-vllm-dsml-recovery.py` — mounted in parity runtime
- `patches/hotfix-vllm-dspark-block-k.py` — mounted in parity runtime
- `patches/hotfix-vllm-dspark-swa-prefix.py` — mounted in parity runtime
- `patches/hotfix-vllm-empty-encoder-output.py` — mounted in parity runtime
- `patches/hotfix-vllm-issue117-shm-ring-buffer.py` — mounted in parity runtime
- `patches/hotfix-vllm-issue136-xgrammar-termination.py` — mounted in parity runtime
- `patches/hotfix-vllm-issue138-responses-history.py` — mounted in parity runtime
- `patches/hotfix-vllm-issue191-toolcall-failclosed.py` — mounted in parity runtime
- `patches/hotfix-vllm-mxfp4-indexer-cache.py` — mounted in parity runtime
- `patches/hotfix-vllm-redact-api-key-log.sh` — mounted in parity runtime
- `patches/hotfix-vllm-rope-swa-fix.py` — mounted in parity runtime
- `patches/keys-concurrency.patch` — mounted in parity runtime
- `patches/official-main-b12x-nvfp4-python.patch` — mounted in parity runtime
- `patches/tp3/apply_tp3_patch.py` — mounted in parity runtime
- `patches/vision_exp/__init__.py` — mounted in parity runtime
- `patches/vision_exp/apply.py` — mounted in parity runtime
- `patches/vision_exp/image_processor.py` — mounted in parity runtime
- `patches/vision_exp/processor.py` — mounted in parity runtime
- `patches/vision_exp/vision.py` — mounted in parity runtime

## Cache mapping

| Upstream path | Node-local backing |
|---|---|
| `/cache/huggingface/tilelang-cache` | `/var/lib/llm-test/jit-cache/tilelang` |
| `/cache/huggingface/triton-cache` | `/var/lib/llm-test/jit-cache/triton` |
| `/cache/huggingface/b12x-cute-cache` | `/var/lib/llm-test/jit-cache/b12x-cute` |
| `/cache/huggingface/vllm-cache` | `/var/lib/llm-test/jit-cache/vllm-cache` |
| `/cache/huggingface/flashinfer` | `/var/lib/llm-test/jit-cache/flashinfer` |
| `/cache/huggingface/nccl-fr` | `/var/lib/llm-test/jit-cache/nccl-fr` |
