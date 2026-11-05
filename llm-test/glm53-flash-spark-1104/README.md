# GLM-5.3-Flash DGX Sparks — TensorFold native recipe 1104 (STAGED)

This is a Kubernetes/Conductor port of [MiaAI-Lab/GLM-5.3-Flash-DGX-Sparks-1104](https://github.com/MiaAI-Lab/GLM-5.3-Flash-DGX-Sparks-1104), pinned at recipe commit `94b72f557268f2ea46852ac03c81119d21f3611e` (upstream `main`). It builds the recipe's TensorFold native Zig/CUDA engine (`f350cd3ea253a042e205746928271f9d8f71a82d`) plus its 105 patches for GB10 `sm_121`. The vision template is vendored from the pinned recipe. The commit move from `3066a3fe` is launch-only (reasoning-effort default, worker-login and TP4 script removals); no `patches/engine/` or `docker/Dockerfile` bytes changed, so the digest-pinned serving image already contains the current engine — rerunning the build Job is provenance-only and produces the same tag.

**Staged; second cutover rolled back through GitOps.** The first diagnosable retry proved both GLM ranks exited before TensorFold launch: chronometer saw `MemAvailable` around 22.3 GiB and sextant around 23.3 GiB against the 100-GiB gate. A review against the recipe's verified `start.sh` path found three launch gaps the previous manifest lacked, now closed in `02-serving.yaml`:

1. **No memory reclamation before the gate.** Upstream refuses to start under `MIN_AVAIL_GIB=100`; the rank started while v14's memory/page cache was still being released and exited 1. Both GLM Deployments now have a bounded privileged cache-reclamation init container matching v14, followed by the rank gate (`GLM_MIN_AVAIL_GIB=100`).
2. **No context auto-fit.** Upstream defaults `CONTEXT=auto`: start at 1,048,576 and, when a rank refuses with its memory figures, restart at the window the refusal allows (`fits: ... --context T`). The manifest hard-coded 1M with no retry. The launcher now parses the refusal, records the fitted window in `/lane-state/glm53-1104-context.tsv` on the shared `model-cache` PVC (min wins, so both ranks' fingerprints agree), and retries smaller — the same convergence `start.sh` gets from its log scraping, coordinated through the PVC instead of both ranks' local state dirs.
3. **Logs were not preserved.** Rank output now appends to the node-local `/var/lib/llm-test/glm53-flash-1104-state/logs/` hostPath, so a terminated container's refusal text survives pod recreation.

Minor parity env (`TF_GLM_W8A8=0`, `TF_GLM_CE_EXCHANGE=0`) and the newer recipe's `--reasoning-effort xhigh` default were added at the same time. The synthetic CUDA checks ran clean for the reference path (`tf-cuda-test glm-ref` passed on sextant); the synthetic mixed-bit `glm-exl3` long-prompt case fails at `tf_exl3_group` on both Sparks (128 KiB dynamic shared request vs the pinned source's 64 KiB registration) — a real upstream kernel defect candidate for long prompts, but not established as the startup-exit cause. Initial transport remains NCCL-only (`TF_ROCE=0`); custom RoCE remains unqualified (OQ-0050).

Image-build v1 failed before BuildKit because the rootless image has no `/bin/bash`; v2 failed loading `docker/Dockerfile` because its local source was not declared. Neither attempt mounted `model-cache` or published an image. v3 succeeded; the failed Job records are retained for logs and expire by TTL.

The model pull completed and its receipt audit verified 83 checkpoint shards (175,642,267,944 bytes) plus one DFlash2 weight file. The pinned puller did not emit `RECEIPT_PATH`, so the Job used its own verified snapshot inventory receipt. The read-only preflight from the active v14 head reported `1813G` available on `/models` before the pull. The attempted cutover did not alter the model cache.

## Recipe pins and staged capacity

- Image: `local-registry.registry.svc.cluster.local:5000/homelab/tensorfold-glm53-flash-1104:74e19a63a9a5-py3-v2@sha256:437559d301f371227a06d32be6fa9800e9d092543d774f694b7e532ac44110a1`. The native BuildKit v3 image is wrapped by a small Python-enabled runtime layer; the derived image passed its stdlib import check and is digest-pinned. The upstream tag remains `74e19a63a9a5` at the pinned recipe commit.
- Checkpoint: `Mia-AiLab/GLM-5.3-Flash-EXL3-4bpw-TensorFold@76c0b5173166d2795dd48860f45d8224817f894c` (~164 GiB).
- Drafter: `incoai/GLM-5.3-Flash-DFlash2@bf582e4eacc1810f76656d1811693ff6c6737d2a`. Its upstream license is CC BY-NC-ND 4.0; do not use for commercial workloads.
- Served profile: TP=2, one Spark per rank, `PARALLEL=8`, `CONTEXT` auto-fit from 1048576 (shared fit file; see status section), FP8 KV pages, q8 dense/head, vision, DFlash2, reasoning effort xhigh, `MEMORY_RESERVE_GIB=9.5`. Upstream defaults to port 8020; this deployment uses the established port 8000.
- Downloader targets the existing `model-cache` PVC. It adds a separate pinned Hugging Face snapshot and does not copy, rename, or delete the existing v14 snapshot. Serving mounts the PVC read-only. This is separate from the DeepSeek ephemeral-cache lane.

## Why this maps to existing workflows

- `00-image-build.yaml` uses the existing rootless BuildKit Job pattern and fetches the upstream recipe at a full immutable commit; the native arm64 build ran on `octant`. v3 uses `/bin/sh` and explicitly declares the `dockerfile` local source.
- `01-download-model.yaml` uses the existing `glm53-cache-puller:v6` downloader, rate-limited to 62.5 MB/s, and verifies the pinned snapshot's index/shards before writing a lane receipt (the pinned image did not emit `RECEIPT_PATH`). It preserves resumable `.part` files and never deletes other model data. After verification, GitOps keeps the one-shot Job suspended and no longer Force/Replace recreates it on every sync.
- The runtime-image v1 attempt (`05-runtime-image-python3-build.yaml`, `python3-minimal` without the `json` stdlib) failed and has been deleted; `06-runtime-image-python3-build-v2.yaml` installs full `python3` and its build verified `ipaddress`, `json`, `pathlib`, and `shlex`. The image build has no GPU or `model-cache` mount.
- `07-fabric-runtime-preflight.yaml` ran successfully on octant against the live v14 peer, verifying node inventory, two rails, and HCA/GID selection. It requests no GPU and mounts no `model-cache`.
- The live smoke Job was removed from the active Kustomization after the retry failed; it is not a serving or cache resource.
- `02-serving.yaml` mirrors the current TensorFold v14 two-rank Kubernetes shape: host networking/IPC, `nvidia-rdma`, node capability scheduling and anti-affinity. Worker rank 1 starts first; its launcher waits for the head rendezvous, so the worker uses `DeploymentAvailable` as the Conductor gate and then Conductor starts head rank 0. The launcher replicates `start.sh`'s memory gate, rank-log preservation and context auto-fit (see the status section above). The initial serving window uses NCCL-only; head health gates the stable route.
- `03-managed-workload.yaml` uses `RecreateTogether` so a rank failure recreates the pair. It is `Standby` pending root-cause of the serving-rank startup failure; its head carries the stable `dgx-spark` alias.

The serving manifest reuses the existing `tensorfold-v14-rdma-fabric` ConfigMap and `/var/lib/dgx-spark/rdma-fabric.json` host inventory. NCCL bootstrap is placed on the shared control-plane address; NCCL/engine data traffic is selected from the node-local RoCE inventory. This is the Kubernetes adaptation to validate; upstream's launcher discovers its direct-link address through SSH.

## Cutover / revert scripts

Run these as yourself (they need ManagedWorkload patch rights; the agent identity cannot patch them):

- `./cutover.sh` — v14 `Standby` → verifies both `spec.desiredState` and Conductor `status.effectiveIntent` are `Standby` → GLM 1104 `Resident` → verifies both intent fields are `Resident` → waits for both ranks (watch loop every 60s) → checks the `glm53-flash-1104-api` endpoint, `/health`, `/v1/models`, and a greedy completion. It does **not** revert automatically on failure or timeout; run `./revert.sh` explicitly. `CUTOVER_TIMEOUT` (default 2700s) bounds the wait.
- `./revert.sh` — 1104 `Standby` → verifies the effective intent → v14 `Resident` → verifies the effective intent → waits for both ranks → verifies `dgx-spark-backend` has an endpoint and answers `/health`. `REVERT_TIMEOUT` (default 2700s).

Both are idempotent. If the worker refuses during a cutover, the cutover script leaves the current state unchanged for inspection; run `./revert.sh` when you decide to restore v14. Read `/var/lib/llm-test/glm53-flash-1104-state/logs/rank1.log` on the worker node — the launcher preserves the refusal text there.

## Activation gates / rollback

1. Keep recipe 1104 `Standby` until an exclusive window: set v14 `Standby`, let its memory release, then activate 1104 and watch `/state/logs/rank*.log` on each rank node — the memory gate, fit file and preserved logs make the next failure diagnosable. Restore v14 `Resident` if the pair does not come up.
2. The serving mounts of `model-cache` remain read-only; the only lane write is the small `glm53-1104-context.tsv` fit file via the dedicated `/lane-state` mount of the same PVC (the same place the pull receipt lives).
3. A retry must remain NCCL-only (`TF_ROCE=0`); do not enable custom RoCE until OQ-0050's rank/GID and cross-rank qualification passes.
4. A future smoke must wait for the recipe API endpoint and then verify `/health`, `/v1/models`, a short completion, both ranks, memory reserve, and the stable Service endpoint after cold load.
5. Roll back through GitOps by setting recipe 1104 `Standby` and v14 `Resident`; never run both TP2 workloads simultaneously.

The image build did not mount or write `model-cache`. The downloader added only the pinned snapshots; serving mounts the PVC read-only. Git manifests keep rank replicas at zero while Conductor owns runtime scale. The stable API Service remains on port 8000 and follows the head's `serving.homelab.io/alias=dgx-spark` label.

## Source and licensing

The pinned recipe is Apache-2.0; its upstream `LICENSE`, `NOTICE.md`, and `CREDITS.md` apply. The vendored vision template is from that exact commit. TensorFold, Hugging Face model weights, and DFlash2 retain their own licenses/terms. See the upstream README and notices before activation.
