# Campfire Kimi-K3.1-Pro quantization (staged scaffold)

**Status: workers suspended; checkpoint provisioning and download approved/in progress.** Both per-Spark worker Jobs remain `suspend: true`, so they create no Pods or claims. Kyle approved a dedicated 2 TiB `juicefs-cache-sc` PVC and the full checkpoint download. A separate downloader Job is staged suspended until its native-amd64 image is built and digest-pinned; it runs only on capstan1, uses the existing model-cache-puller and resumable `.part` files, then verifies the checkpoint before publishing `/models/kimi-k31`.

## Verified upstream facts (2026-11-26)

- Project: `kimi-k31-pmul1x-f16`; upstream title: “Kimi-K3.1-Pro, pmul1x-f16 at K1.5, K2 and K2.5”.
- Public jobs API snapshot (2026-11-26) reported 82,524 total slots; 7,111 uploaded; 85 claimed; 10,744 open; 64,584 not ready; `disabled=0`. The project page rendered “Hessians up, claims off” during the same period, so verify current claims status again before starting workers. These are snapshots, not a deployment promise. Poll no faster than upstream's 5–15 minute guidance; its public API is cached for 20 seconds.
- Checkpoint: Hugging Face `moonshotai/Kimi-K3.1-Pro`, immutable revision `80aff651e9b2d2f5b9f70f92a0a7a77054418e16`; upstream checkpoint identity is SHA-256 `fd60deec1f24953995872744cf085c3cdae261e73fd203046e5f74f6ee9d9c79` over the concatenated `config.json` and `model.safetensors.index.json` bytes (the upstream command uses `cat ... | sha256sum`).
- Encoder: `ghcr.io/kindlingai/exlr8enc:latest`, published for `linux/arm64` and GB10. The canonical documented invocation uses `site --watch --key-file /key --bf16 /models/NAME`; project-specific invocation also supplies `--job kimi-k31-pmul1x-f16`. Image digest must be resolved and tested before any worker starts.
- API key requires GitHub login, account owner approval, then creation on the project's page. There are no project Hessian artifacts to download according to the live project status; Hessians are already up. Upstream documentation does not specify Hugging Face auth as required.
- A stopped encoder's claims may remain held for 12 hours. Upstream documents `GET /api/claims`, per-claim `DELETE /api/claims/JOB/LAYER/EXPERT`, and release-all `DELETE /api/claims` (authenticated). Do not run release-all for a worker because it could release claims owned by another worker/account. No verified graceful signal/claim-handoff contract was found; do not assume Kubernetes termination safely releases claims.

## Account setup (Kyle)

1. Sign in at <https://campfire.kindlingai.dev> with GitHub and request/await account approval.
2. On the project page, create an API key. Upstream says the key is sent only to Campfire as `Authorization: Bearer KEY`; never put it in Git, a command argument, logs, or chat.
3. Once approved, we will place it in OpenBao KV v2 at mount `k8s`, path `campfire/kimi-k31/worker-a`, field `api-key` (and optionally a separate `worker-b` path/key if the site confirms multiple keys per account are supported). The active manifest should use VSO to project only that field into a read-only Secret file. No key has been supplied or requested in chat.

You can set up the account now; no cluster changes, downloads, PVC allocation, or workers have been performed. Tell me when approval and key creation are complete, but do not send the key here.

## Storage design

Use the existing ephemeral/cache JuiceFS tier, `juicefs-cache-sc`, not the backed-up `juicefs-sc`. That tier uses its separate `juicefs-mc-cache` filesystem/backend. The cluster currently configures its DGX peer cache ring only for PVC `model-cache-ephemeral-v2` (group `dgx-model-cache-ephemeral`, port 13913); a Campfire PVC needs its own explicitly scoped CSI `pvcSelector` patch and a distinct cache-group name/port. Do not reuse the serving checkpoint's ring group across different JuiceFS filesystems, and do not change broad/global CSI settings.

The pinned HF repository inventory has 96 `.safetensors` shards totaling 1,561,293,160,568 bytes plus 62,806,763 bytes of auxiliary files (112 files total; 1,561,355,967,331 bytes overall, about 1.561 TB / 1.420 TiB). Kyle approved a 2 TiB PVC, leaving about 0.58 TiB headroom above the published snapshot. Backend billing/egress rates are not exposed by this cluster; no cost claim is made. The separate downloader runs on capstan1 (amd64, no GPU) while Spark nodes are busy. It uses the repository's existing model-cache-puller, disables Xet so the in-code aggregate token-bucket cap holds, and sets `RATE=106250000` bytes/s (85% of nominal 1 Gbit/s, approximately 4.1 hours at the cap; actual time may be 4–5+ hours depending on HF and JuiceFS throughput). The Job resumes `.part` files after interruption. It verifies all 96 shard byte sizes and upstream's config/index identity hash, then creates the `/models/kimi-k31` symlink and completion receipt; workers mount the PVC read-only and require the marker. Full snapshot only: partial-shard safety is not upstream-verified.

During download, the CSI mountPodPatch is explicitly PVC-scoped and uses the plain cache-tier mount on capstan1 (no cache ring). After download completes, remove the completed downloader Job/pod before changing mount options; then apply a PVC-specific cache-ring patch and verify the JuiceFS mount on the Spark nodes before resuming workers. The volume uses the existing cache-tier `juicefs-mc-cache` filesystem; ring membership must match this exact filesystem. Do not touch global JuiceFS configuration or other PVCs.

The JuiceFS CSI mount cache is not a quota for model storage. Reuse the established `/mnt/pool/juicefs-ring` cache infrastructure, but choose group/port/cache size after checking existing cache-ring membership, available local NVMe, and host/network capacity. Do not alter the global ring for this workload.

## Current staged resources

- GitOps base includes namespace `campfire-kimi-k31`, PriorityClass `campfire-volunteer` (`value: -10`, `preemptionPolicy: Never`), an approved 2 TiB RWX PVC on `juicefs-cache-sc`, an amd64 puller-image build Job on capstan1, a **suspended** download Job, and two independent, **suspended** finite worker Jobs pinned to chronometer and sextant.
- Each Job requests one `nvidia.com/gpu`, mounts the eventual shared model PVC read-only, consumes `/run/campfire/api-key` from Secret `campfire-api` read-only, uses local scratch, disables service-account token automount, and uses the upstream `site --watch --job kimi-k31-pmul1x-f16 --key-file ... --bf16 ...` command.
- Worker image is temporarily the upstream `:latest` tag because anonymous GHCR manifest resolution returned HTTP 401. The Jobs MUST remain suspended until the user provides GHCR `read:packages` access, the ARM64 digest is verified, and the image can be pulled. Add an imagePullSecret only through OpenBao/VSO or another approved secret flow.
- Downloader image is built natively for capstan1/amd64 from the pinned homelab source commit and pushed to the internal registry. Its output digest must be verified and set in `download-job.yaml` before that Job is unsuspended. This extra build is necessary because the current model-cache-puller:v7 digest is arm64-only while capstan1 is amd64.
- The downloader is separate because upstream expects weights already on disk (`hf download ... --revision ... --local-dir ...`); the encoder does not fetch this checkpoint itself. HF auth is not configured because the model repo is public; re-evaluate only if download returns an actual access denial.
- The Campfire API key VSO projection is still pending account approval/key setup. Encoder Jobs remain suspended; GHCR pull access and a digest-pinned tested image are also required before worker activation.
- No NCCL/MPI/Ray/tensor parallelism: workers independently claim queue slots. Do not auto-switch to other projects or auto-delete the PVC.

Node inventory (read-only, current): `chronometer`, `sextant`, and `octant` are DGX Spark/NVIDIA nodes; `nvidia-device-plugin` is running on all three. Existing serving work currently occupies the Sparks, including GLM-5.3-Flash B-lane pods on chronometer/sextant. This workload must not be enabled until the operator confirms the GLM lane is spun down and the GPU scheduling/priority behavior is validated. Cluster MCP identity cannot list cluster-scoped PriorityClasses; use the GitOps source to select a non-disruptive priority rather than inventing one.

## Bring-up gates

1. Kyle confirms the GLM-5.3-Flash B lane is stopped and approves the measured storage/download budget.
2. Confirm Campfire approval, claims enabled, remaining open slots, Hessian readiness, and the exact project `weights` data from `/api/jobs`; confirm the project page and API agree.
3. Resolve model snapshot total size and referenced shard list at the pinned revision. Confirm no special license/access gating; download cost is approved.
4. Identify tested ARM64 encoder image digest and its CLI/termination behavior. Run image/GPU compatibility check on one Spark without claiming work.
5. Build/apply the CSI PVC-specific cache-ring change and temporary PVC; validate mount and local cache behavior without disturbing serving data.
6. VSO key projection works without exposing value; validate authenticated read-only project access. Do not log headers or secret content.
7. Run one canary worker, observe at least 30–60 minutes (or enough accepted slots), verify Campfire acceptance and record actual performance before starting the second Spark.

## Runbook (after activation)

Commands must use one line when handed to the operator. Expected names/fields are finalized during activation; do not use these commands until resources exist.

- Download progress: `kubectl --context mc -n campfire-kimi-k31 logs job/campfire-kimi-k31-download -f`
- Worker logs: `kubectl --context mc -n campfire-kimi-k31 logs job/campfire-kimi-k31-worker-a -f`
- GPU use: `kubectl --context mc top nodes chronometer sextant` (supplement with node `nvidia-smi` telemetry via existing monitoring; do not add host mounts or privileged access just for telemetry).
- Contribution/status: check the project's public page/API at <https://campfire.kindlingai.dev/jobs/kimi-k31-pmul1x-f16> and attribute only accepted uploads to these workers.
- Scale to zero / suspend: suspend or delete the two worker Jobs after recording their owned claims; never run account-wide release-all. Follow upstream's per-claim release only for claims explicitly verified as owned by that worker.
- Resume: validate checkpoint receipt, current open slots/claims status and credentials, then recreate workers.
- Cleanup: stop workers; verify no owned claims remain (or document their 12-hour expiry); keep the PVC until work is resolved and Kyle explicitly approves deletion. The JuiceFS StorageClass has `reclaimPolicy: Retain`, so PVC deletion alone does not guarantee backend reclamation. Reclaim only the project-specific JuiceFS volume after independent identity/path verification; never run filesystem-wide GC or delete shared datasets.

## Open validation items

- Upstream does not define the server-side claim lease renewal/expiry interval beyond the observed 12-hour hold after stopping, safe signal handling, per-key concurrency semantics, or a resumable slot protocol. Verify these against the encoder's actual release/source before designing termination and retries.
- The skill has no download-shard selection contract; use full checkpoint until selective loading is confirmed safe.
- Digest pinning and GB10 execution smoke-test still required; `latest` is only upstream's suggested pull command, not a reproducible deployment pin.
- Monitoring/log retention should use current Alloy/Grafana infrastructure; add no separate log stack.
