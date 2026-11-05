# GLM-5.3-Flash DGX Sparks — TensorFold native recipe 1104 (STAGED)

This is a Kubernetes/Conductor port of [MiaAI-Lab/GLM-5.3-Flash-DGX-Sparks-1104](https://github.com/MiaAI-Lab/GLM-5.3-Flash-DGX-Sparks-1104), pinned at recipe commit `3066a3fe49e7fcdf969de9a51094dd8985cec1a0`. It builds the recipe's TensorFold native Zig/CUDA engine (`f350cd3ea253a042e205746928271f9d8f71a82d`) plus its 105 patches for GB10 `sm_121`. The vision template is vendored from that same pinned recipe.

**Staged; second cutover rolled back through GitOps.** The Python-enabled image's read-only preflight passed on octant, but the serving worker on sextant exited before a healthy head or stable endpoint appeared. The live smoke Job also failed while the API had no endpoints. v14 is being restored to `Resident`; GLM returns to `Standby`. Do not retry until the actual rank startup failure is root-caused. The model-pull Job re-ran inventory verification only (0 files queued); it did not redownload weights. Initial transport remains NCCL-only (`TF_ROCE=0`); custom RoCE remains unqualified (OQ-0050).

Image-build v1 failed before BuildKit because the rootless image has no `/bin/bash`; v2 failed loading `docker/Dockerfile` because its local source was not declared. Neither attempt mounted `model-cache` or published an image. v3 succeeded; the failed Job records are retained for logs and expire by TTL.

The model pull completed and its receipt audit verified 83 checkpoint shards (175,642,267,944 bytes) plus one DFlash2 weight file. The pinned puller did not emit `RECEIPT_PATH`, so the Job used its own verified snapshot inventory receipt. The read-only preflight from the active v14 head reported `1813G` available on `/models` before the pull. The attempted cutover did not alter the model cache.

## Recipe pins and staged capacity

- Image: `local-registry.registry.svc.cluster.local:5000/homelab/tensorfold-glm53-flash-1104:74e19a63a9a5-py3-v2@sha256:437559d301f371227a06d32be6fa9800e9d092543d774f694b7e532ac44110a1`. The native BuildKit v3 image is wrapped by a small Python-enabled runtime layer; the derived image passed its stdlib import check and is digest-pinned. The upstream tag remains `74e19a63a9a5` at the pinned recipe commit.
- Checkpoint: `Mia-AiLab/GLM-5.3-Flash-EXL3-4bpw-TensorFold@76c0b5173166d2795dd48860f45d8224817f894c` (~164 GiB).
- Drafter: `incoai/GLM-5.3-Flash-DFlash2@bf582e4eacc1810f76656d1811693ff6c6737d2a`. Its upstream license is CC BY-NC-ND 4.0; do not use for commercial workloads.
- Served profile: TP=2, one Spark per rank, `PARALLEL=8`, `CONTEXT=1048576`, FP8 KV pages, q8 dense/head, vision, DFlash2, `MEMORY_RESERVE_GIB=9.5`. Upstream defaults to port 8020; this deployment uses the established port 8000.
- Downloader targets the existing `model-cache` PVC. It adds a separate pinned Hugging Face snapshot and does not copy, rename, or delete the existing v14 snapshot. Serving mounts the PVC read-only. This is separate from the DeepSeek ephemeral-cache lane.

## Why this maps to existing workflows

- `00-image-build.yaml` uses the existing rootless BuildKit Job pattern and fetches the upstream recipe at a full immutable commit; the native arm64 build ran on `octant`. v3 uses `/bin/sh` and explicitly declares the `dockerfile` local source.
- `01-download-model.yaml` uses the existing `glm53-cache-puller:v6` downloader, rate-limited to 62.5 MB/s, and verifies the pinned snapshot's index/shards before writing a lane receipt (the pinned image did not emit `RECEIPT_PATH`). It preserves resumable `.part` files and never deletes other model data.
- The runtime-image v1 attempt installed only `python3-minimal` and failed because it omitted the standard-library `json` module. `06-runtime-image-python3-build-v2.yaml` installs full `python3`; its successful build verified `ipaddress`, `json`, `pathlib`, and `shlex`. The image build has no GPU or `model-cache` mount.
- `07-fabric-runtime-preflight.yaml` ran successfully on octant against the live v14 peer, verifying node inventory, two rails, and HCA/GID selection. It requests no GPU and mounts no `model-cache`.
- The live smoke Job was removed from the active Kustomization after the retry failed; it is not a serving or cache resource.
- `02-serving.yaml` mirrors the current TensorFold v14 two-rank Kubernetes shape: host networking/IPC, `nvidia-rdma`, node capability scheduling and anti-affinity. Worker rank 1 starts first; Conductor gates it on containers running, not readiness, then starts head rank 0. The initial cutover uses NCCL-only; head health gates the stable route.
- `03-managed-workload.yaml` uses `RecreateTogether` so a rank failure recreates the pair. It is `Resident` for this coordinated retry; its head carries the stable `dgx-spark` alias.

The serving manifest reuses the existing `tensorfold-v14-rdma-fabric` ConfigMap and `/var/lib/dgx-spark/rdma-fabric.json` host inventory. NCCL bootstrap is placed on the shared control-plane address; NCCL/engine data traffic is selected from the node-local RoCE inventory. This is the Kubernetes adaptation to validate; upstream's launcher discovers its direct-link address through SSH.

## Activation gates / rollback

1. The Python-enabled runtime preflight passed on octant against the live v14 peer, but did not validate startup on the actual rank nodes.
2. Keep recipe 1104 `Standby` until the sextant worker exit is root-caused and the launch script passes on the serving ranks; v14 must be fully Ready with its stable endpoint before any retry.
3. A retry must remain NCCL-only (`TF_ROCE=0`); do not enable custom RoCE until OQ-0050's rank/GID and cross-rank qualification passes.
4. A future smoke must wait for the recipe API endpoint and then verify `/health`, `/v1/models`, a short completion, both ranks, memory reserve, and the stable Service endpoint after cold load.
5. Roll back through GitOps by setting recipe 1104 `Standby` and v14 `Resident`; never run both TP2 workloads simultaneously.

The image build did not mount or write `model-cache`. The downloader added only the pinned snapshots; serving mounts the PVC read-only. Git manifests keep rank replicas at zero while Conductor owns runtime scale. The stable API Service remains on port 8000 and follows the head's `serving.homelab.io/alias=dgx-spark` label.

## Source and licensing

The pinned recipe is Apache-2.0; its upstream `LICENSE`, `NOTICE.md`, and `CREDITS.md` apply. The vendored vision template is from that exact commit. TensorFold, Hugging Face model weights, and DFlash2 retain their own licenses/terms. See the upstream README and notices before activation.
