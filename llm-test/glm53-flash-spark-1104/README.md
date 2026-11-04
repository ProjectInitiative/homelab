# GLM-5.3-Flash DGX Sparks — TensorFold native recipe 1104 (STAGED)

This is a Kubernetes/Conductor port of [MiaAI-Lab/GLM-5.3-Flash-DGX-Sparks-1104](https://github.com/MiaAI-Lab/GLM-5.3-Flash-DGX-Sparks-1104), pinned at recipe commit `3066a3fe49e7fcdf969de9a51094dd8985cec1a0`. It builds the recipe's TensorFold native Zig/CUDA engine (`f350cd3ea253a042e205746928271f9d8f71a82d`) plus its 105 patches for GB10 `sm_121`. The vision template is vendored from that same pinned recipe.

**Not activated.** This directory is intentionally not in `apps.yaml`, the root Argo tree, or `llm-test/conductor-workloads/kustomization.yaml`. Both Jobs below are `suspend: true`; both Deployments have zero replicas; the separate Conductor object is `Standby`. No build, download, or serving workload runs from this commit.

## Recipe pins and staged capacity

- Image: `local-registry.registry.svc.cluster.local:5000/homelab/tensorfold-glm53-flash-1104:74e19a63a9a5`. The tag is the output of the upstream `scripts/prepare.sh --label` at the pinned recipe commit; it includes the engine patch set and Dockerfile inputs. It is not a published digest yet.
- Checkpoint: `Mia-AiLab/GLM-5.3-Flash-EXL3-4bpw-TensorFold@76c0b5173166d2795dd48860f45d8224817f894c` (~164 GiB).
- Drafter: `incoai/GLM-5.3-Flash-DFlash2@bf582e4eacc1810f76656d1811693ff6c6737d2a`. Its upstream license is CC BY-NC-ND 4.0; do not use for commercial workloads.
- Default served profile from the recipe: TP=2, one Spark per rank, `PARALLEL=8`, `CONTEXT=1048576`, FP8 KV pages, q8 dense/head, vision, DFlash2, `MEMORY_RESERVE_GIB=9.5`, port 8020.
- Downloader targets the existing `model-cache` PVC. It adds a separate pinned Hugging Face snapshot and does not copy, rename, or delete the existing v14 snapshot. Serving mounts the PVC read-only. This is separate from the DeepSeek ephemeral-cache lane.

## Why this maps to existing workflows

- `00-image-build.yaml` uses the existing rootless BuildKit Job pattern and fetches the upstream recipe at a full immutable commit; the build is native arm64 and prefers idle `octant`.
- `01-download-model.yaml` uses the existing `glm53-cache-puller:v6` downloader, rate-limited to 62.5 MB/s, and verifies the pinned snapshot's index/shards before writing a receipt. It preserves resumable `.part` files and never deletes other model data.
- `02-serving.yaml` mirrors the current TensorFold v14 two-rank Kubernetes shape: host networking/IPC, `nvidia-rdma`, node capability scheduling and anti-affinity. Worker rank 1 starts first; Conductor gates it on containers running, not readiness, then starts head rank 0. Head health is the serving qualification.
- `03-managed-workload.yaml` uses `RecreateTogether` so a rank failure recreates the pair. It stays `Standby` and does not claim the active `dgx-spark` route.

The serving manifest reuses the existing `tensorfold-v14-rdma-fabric` ConfigMap and `/var/lib/dgx-spark/rdma-fabric.json` host inventory. NCCL bootstrap is placed on the shared control-plane address; NCCL/engine data traffic is selected from the node-local RoCE inventory. This is the Kubernetes adaptation to validate; upstream's launcher discovers its direct-link address through SSH.

## Review / activation sequence

1. Keep this directory unregistered while the current CSI mount/metadata recovery and the existing TensorFold recovery are unsettled.
2. Review the host-network/ConnectX-7 adaptation and ensure the shared RDMA ConfigMap remains available.
3. Register this directory as an Argo Application. Jobs remain suspended and Deployments remain at zero.
4. Intentionally unsuspend the image-build Job, wait for success, and record the pushed image digest; update the serving image from the tag to that immutable digest.
5. Intentionally unsuspend the model-pull Job. It writes only to `model-cache`; confirm the receipt and available space before doing so.
6. Keep the workload in `Standby` until the recipe image, checkpoint, and fabric have been reviewed. To activate, coordinate the exclusive GPU pair with v14: put the old workload in `Standby` before making this one `Resident`. Do not run both TP2 workloads at once.
7. Validate `/health`, `/v1/models`, an image request, memory reserve, and both rank logs before changing any serving alias.

No live cache or serving resource was changed while staging this proposal.

## Source and licensing

The pinned recipe is Apache-2.0; its upstream `LICENSE`, `NOTICE.md`, and `CREDITS.md` apply. The vendored vision template is from that exact commit. TensorFold, Hugging Face model weights, and DFlash2 retain their own licenses/terms. See the upstream README and notices before activation.
