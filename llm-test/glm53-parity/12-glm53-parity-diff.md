# GLM-5.3-Flash EXL3 — MIAI Kubernetes parity lane

- Upstream: `https://github.com/MiaAI-Lab/GLM-5.3-Flash-EXL3-2x-DGX-Sparks`
- Reviewed source: `d0b960816ba15c37927247ff74a6d04e59b00a3e`
- Image baseline: `9348755653f6f8cda5d56562c05462724c40fcbd`
- Image: `ghcr.io/miaai-lab/glm-5.3-flash-2x-dgx-sparks:exl3-instanttensor@sha256:447114ee77d14c9b4732ee23978ada2a0ee9027868a231d6fd42700a8b25be1d`
- Model: `Mia-AiLab/GLM-5.3-Flash-EXL3-TR3-4bpw` @ `25a44fdbf16862a46b7cc9921142c6c81350af2f`
- Draft: `incoai/GLM-5.3-Flash-DFlash2` @ `dc77ff1c99eeb2df044ee3d4f0094eb033fee410`
- Served model id: `GLM-5.3-Flash-EXL3`

## Difference classification

| Area | Classification | Details |
| Image and source overlays | REVIEWED HYBRID | The immutable public image is unchanged. Nine source-only files from `d0b9608` are mounted by exact ConfigMap key on both ranks and applied in upstream order. Native thin-decode is not enabled. |
| Runtime profile | LOCAL POLICY | 512k context, 16 sequences, 2048 batched tokens, 0.88 utilization, and an explicit 15 GiB KV pool are used. `GLM53_INDEXER_WORKSPACE=rightsize`; `GLM53_KDA_BF16_LARGE_M=0`; `GLM53_DRAFT_KV_COMPACT=0`. |
| Model preparation | MODEL PREP EXCEPTION | Pinned snapshots are mounted from the shared `model-cache` PVC and checked by init containers. |
| Kubernetes orchestration | K8S PLATFORM ADAPTER | The `nvidia-rdma` RuntimeClass, GPU/RDMA resources, required anti-affinity, host networking/IPC, headless rendezvous Services, worker-before-head activation, and node-local RoCE discovery translate upstream's two-host launcher without node pinning. |
| Boot warmup | K8S PLATFORM ADAPTER | Upstream warmup runs after `/health`; completion gates head readiness. |

## Effective memory changes

- `patch_mamba_align_chunking.py` aligns prefill checkpoints to the Mamba block.
- `patch_mamba_align_state_free.py` releases all superseded align-state blocks and corrects resident-page accounting, preventing growth during long asynchronous prefills.
- Disabling `GLM53_KDA_BF16_LARGE_M` avoids retaining approximately 3.29 GiB/rank.
- Compact DFlash pages remain off because they reduce allocator block-ID pressure, not backing VRAM.
- The existing right-sized indexer workspace and multimodal processor cache cap remain active.

## Pinned profile

- `PORT=8000`, `TP=2`, `NNODES=2`, `MASTER_PORT=29521`
- `MAX_MODEL_LEN=512000`, `GPU_MEM_UTIL=0.88`, `MAX_NUM_SEQS=16`, `MAX_NUM_BATCHED_TOKENS=2048`
- `KV_CACHE_DTYPE=fp8`, `QUANTIZATION=exl3`, `SPEC_METHOD=dflash`, `DFLASH_TOKENS=7`, `DFLASH_DRAFT_TP=2`
- `LANGUAGE_MODEL_ONLY=0`, `SKIP_MM_PROFILING=1`, `LIMIT_MM={"image":48,"video":1}`
- `MM_IMAGE_TOKENS=2048`, `MM_PROCESSOR_CACHE_GB=1`
- `EXTRA_ARGS=--cudagraph-capture-sizes 1 2 3 4 5 8 16 24 32 --kv-cache-memory-bytes 16106127360`
- CX7: the common Kubernetes interface carries rendezvous; the node-local fabric inventory and sysfs select the two peer-facing HCAs and their RoCE v2 IPv4 GID dynamically

Both checked-in Deployments remain `replicas: 0`. Imperative activation must stop
head before worker, apply the assets and Deployments, then start worker before head.
