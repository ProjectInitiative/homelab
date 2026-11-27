# Campfire Kimi-K3.1-Pro quantization (staged scaffold)

**Status: both unsuspended, unpinned worker Jobs are running with the refreshed key.** Scheduler selected chronometer and sextant; both Pods are Ready with zero restarts. Each worker has completed two layer-16 expert uploads of 24.8 MB (A: experts 727, 198; B: 804, 291). Latest public aggregate: uploaded 13,812; claimed 154; open 3,974; 13 layers done (not all attributable to these workers). Chronometer's 30-request probe to `quant.kindlingai.dev` had 24 HTTP responses, 3 DNS failures and 3 other connection failures. CoreDNS is 3/3 Ready with low CPU and no recent restarts; no DNS restart performed. `--watch` remains active; continue monitoring.

## Verified upstream facts (2026-11-26)

- Project: `kimi-k31-pmul1x-f16`; upstream title: “Kimi-K3.1-Pro, pmul1x-f16 at K1.5, K2 and K2.5”.
- Public jobs API snapshot (2026-11-26) reported 82,524 total slots; 7,111 uploaded; 85 claimed; 10,744 open; 64,584 not ready; `disabled=0`. The project page rendered “Hessians up, claims off” during the same period, so verify current claims status again before starting workers. These are snapshots, not a deployment promise. Poll no faster than upstream's 5–15 minute guidance; its public API is cached for 20 seconds.
- Checkpoint: Hugging Face `moonshotai/Kimi-K3.1-Pro`, immutable revision `80aff651e9b2d2f5b9f70f92a0a7a77054418e16`; upstream checkpoint identity is SHA-256 `fd60deec1f24953995872744cf085c3cdae261e73fd203046e5f74f6ee9d9c79` over the concatenated `config.json` and `model.safetensors.index.json` bytes (the upstream command uses `cat ... | sha256sum`).
- Encoder launcher: `registry.taildeab2.ts.net/homelab/campfire-exlr8-quant:arm64-20261127@sha256:dc46472f1e85cdbd6c604877289457e305eaa67bb806451600a081a24b877743`, built natively on chronometer and pulled back as `linux/arm64`. It wraps the official `exlr8-quant.sh` (pinned SHA-256 `89de834b9060fe3af5b2fbf16080b65ecd457ffb84728c7bffb9be597d3bba5d`); at runtime the script fetches the latest Campfire encoder binary and verifies its published SHA-256. The invocation is `site --watch --job kimi-k31-pmul1x-f16 --key-file /key --bf16 /models/NAME`. After the Secret refresh, the read-only auth probe returned HTTP 200. Both workers have completed two layer-16 expert uploads each (24.8 MB per upload); monitor sustained throughput and intermittent DNS retries.
- API key requires GitHub login, account owner approval, then creation on the project's page. There are no project Hessian artifacts to download according to the live project status; Hessians are already up. Upstream documentation does not specify Hugging Face auth as required.
- A stopped encoder's claims may remain held for 12 hours. Upstream documents `GET /api/claims`, per-claim `DELETE /api/claims/JOB/LAYER/EXPERT`, and release-all `DELETE /api/claims` (authenticated). Do not run release-all for a worker because it could release claims owned by another worker/account. No verified graceful signal/claim-handoff contract was found; do not assume Kubernetes termination safely releases claims.

## Account setup (Kyle)

1. Sign in at <https://campfire.kindlingai.dev> with GitHub and request/await account approval.
2. On the project page, create an API key. Upstream says the key is sent only to Campfire as `Authorization: Bearer KEY`; never put it in Git, a command argument, logs, or chat.
3. Once approved, place the shared key in OpenBao KV v2 at mount `k8`, path `campfire/kimi-k31/workers`, field `api-key`. The Campfire catalog config generates a VaultAuth and VaultStaticSecret that projects only `api-key` into the read-only Kubernetes Secret `campfire-api` in namespace `llm-test`; both workers mount it at `/run/campfire/api-key`. Do not send the key in chat.

Kyle recreated `Secret/campfire-api` from the website key file; a byte-for-byte local-file comparison matched, and an in-cluster authenticated GET returned HTTP 200. VSS still reports 403 permission denied reading the OpenBao KV path; the manual Secret works independently of VSO. Never print its value.

## Storage design

Use the existing ephemeral/cache JuiceFS tier, `juicefs-cache-sc`, not the backed-up `juicefs-sc`. That tier uses its separate `juicefs-mc-cache` filesystem/backend. The cluster currently configures its DGX peer cache ring only for PVC `model-cache-ephemeral-v2` (group `dgx-model-cache-ephemeral`, port 13913); a Campfire PVC needs its own explicitly scoped CSI `pvcSelector` patch and a distinct cache-group name/port. Do not reuse the serving checkpoint's ring group across different JuiceFS filesystems, and do not change broad/global CSI settings.

The pinned HF repository inventory has 96 `.safetensors` shards totaling 1,561,293,160,568 bytes plus 62,806,763 bytes of auxiliary files (112 files total; 1,561,355,967,331 bytes overall, about 1.561 TB / 1.420 TiB). Kyle approved a 2 TiB PVC, leaving about 0.58 TiB headroom above the published snapshot. Backend billing/egress rates are not exposed by this cluster; no cost claim is made. The separate downloader runs on capstan1 (amd64, no GPU) while Spark nodes are busy. It uses the repository's existing model-cache-puller, disables Xet so the in-code aggregate token-bucket cap holds, and sets `RATE=106250000` bytes/s (85% of nominal 1 Gbit/s, approximately 4.1 hours at the cap; actual time may be 4–5+ hours depending on HF and JuiceFS throughput). The Job resumes `.part` files after interruption. It verifies all 96 shard byte sizes and upstream's config/index identity hash, then creates the `/models/kimi-k31` symlink and completion receipt; workers mount the PVC read-only and require the marker. Full snapshot only: partial-shard safety is not upstream-verified.

During download, the CSI mountPodPatch is explicitly PVC-scoped and uses the plain cache-tier mount on capstan1 (no cache ring). After download completes, remove the completed downloader Job/pod before changing mount options; then apply a PVC-specific cache-ring patch and verify the JuiceFS mount on the Spark nodes before resuming workers. The volume uses the existing cache-tier `juicefs-mc-cache` filesystem; ring membership must match this exact filesystem. Do not touch global JuiceFS configuration or other PVCs.

The JuiceFS CSI mount cache is not a quota for model storage. Reuse the established `/mnt/pool/juicefs-ring` cache infrastructure, but choose group/port/cache size after checking existing cache-ring membership, available local NVMe, and host/network capacity. Do not alter the global ring for this workload.

## Current staged resources

- The Argo app now targets `llm-test`, where the active direct downloader's 2 TiB RWX PVC already lives. `pvc.yaml` declares that exact claim for Argo adoption (same name, namespace, StorageClass, access mode, and size); the legacy `campfire-kimi-k31` namespace/PVC remain explicitly retained and are not used by these workers. The base also includes PriorityClass `campfire-volunteer` (`value: -10`, `preemptionPolicy: Never`), a puller-image build Job, a separately named **suspended** staged downloader, and two independent finite worker Jobs selecting eligible ARM64 DGX/NVIDIA nodes without hostname pinning.
- Each worker requests one `nvidia.com/gpu`, mounts the adopted `llm-test/campfire-kimi-k31-models` PVC read-only, consumes `/run/campfire/api-key` from Secret `campfire-api` read-only, uses local scratch, disables service-account token automount, and uses the upstream `site --watch --job kimi-k31-pmul1x-f16 --key-file ... --bf16 ...` command.
- Both worker specs use the internally mirrored, digest-pinned ARM64 launcher and select any eligible DGX/NVIDIA node. The latest Pods run on chronometer and sextant; each completed two uploads. A 30-request probe from chronometer observed 3 DNS failures and 3 other connection failures; CoreDNS replicas remain healthy. Investigate upstream forwarding before any DNS restart.
- Downloader image is built natively for capstan1/amd64 from the pinned homelab source commit and pushed to the internal registry. Its output digest must be verified and set in `download-job.yaml` before that Job is unsuspended. This extra build is necessary because the current model-cache-puller:v7 digest is arm64-only while capstan1 is amd64.
- The downloader is separate because upstream expects weights already on disk (`hf download ... --revision ... --local-dir ...`); the encoder does not fetch this checkpoint itself. HF auth is not configured because the model repo is public; re-evaluate only if download returns an actual access denial.
- The Campfire VSO projection is configured, but its status is `SecretSynced=False` with HTTP 403 permission denied for `production/k8/data/campfire/kimi-k31/workers`. The manually created Secret passes authenticated read-only access; VSO policy remains a separate issue.
- No NCCL/MPI/Ray/tensor parallelism: workers independently claim queue slots. Do not auto-switch to other projects or auto-delete the PVC.

Node inventory: `chronometer`, `sextant`, and `octant` are DGX Spark/NVIDIA nodes. Kyle confirms chronometer and sextant are available for Campfire workers; GLM remains on other nodes and does not need to be stopped for this placement. Verify current GPU allocation and scheduling before activation. Cluster MCP identity cannot list cluster-scoped PriorityClasses; use the GitOps source to select a non-disruptive priority rather than inventing one.

## Bring-up gates

1. Confirm chronometer and sextant remain free for Campfire; Kyle reports GLM is on other nodes, so it may remain running.
2. Confirm Campfire approval, claims enabled, remaining open slots, Hessian readiness, and the exact project `weights` data from `/api/jobs`; confirm the project page and API agree.
3. **Complete:** checkpoint identity, all 96 shard sizes, and total bytes verified at the pinned revision; no special license/access gate was encountered.
4. **Image built and digest-pinned:** run `site --help`/GPU compatibility smoke on one Spark without a key or Campfire claim; confirm the projected API Secret is Ready.
5. Build/apply the CSI PVC-specific cache-ring change and temporary PVC; validate mount and local cache behavior without disturbing serving data.
6. The manually created Secret currently passes authenticated read-only project access; VSO projection remains 403. Do not log headers or secret content.
7. Both workers were started at Kyle's direction after key refresh. Observe at least 30–60 minutes (or enough accepted slots), verify Campfire acceptance and record actual performance.

## Runbook (after activation)

Commands must use one line when handed to the operator. Expected names/fields are finalized during activation; do not use these commands until resources exist.

- Download progress: `kubectl --context mc -n llm-test logs job/campfire-kimi-k31-download -f`
- Worker logs: `kubectl --context mc -n llm-test logs job/campfire-kimi-k31-worker-a-arm64 -f`
- GPU use: `kubectl --context mc top nodes chronometer sextant` (supplement with node `nvidia-smi` telemetry via existing monitoring; do not add host mounts or privileged access just for telemetry).
- Contribution/status: check the project's public page/API at <https://campfire.kindlingai.dev/jobs/kimi-k31-pmul1x-f16> and attribute only accepted uploads to these workers.
- Scale to zero / suspend: suspend or delete the two worker Jobs after recording their owned claims; never run account-wide release-all. Follow upstream's per-claim release only for claims explicitly verified as owned by that worker.
- Resume: validate checkpoint receipt, current open slots/claims status and credentials, then recreate workers.
- Cleanup: stop workers; verify no owned claims remain (or document their 12-hour expiry); keep the PVC until work is resolved and Kyle explicitly approves deletion. The JuiceFS StorageClass has `reclaimPolicy: Retain`, so PVC deletion alone does not guarantee backend reclamation. Reclaim only the project-specific JuiceFS volume after independent identity/path verification; never run filesystem-wide GC or delete shared datasets.

## Open validation items

- Upstream does not define the server-side claim lease renewal/expiry interval beyond the observed 12-hour hold after stopping, safe signal handling, per-key concurrency semantics, or a resumable slot protocol. Verify these against the encoder's actual release/source before designing termination and retries.
- The skill has no download-shard selection contract; use full checkpoint until selective loading is confirmed safe.
- Runtime, authenticated API access, and one successful upload from each worker are verified. Continue monitoring for sustained work and DNS errors.
- Monitoring/log retention should use current Alloy/Grafana infrastructure; add no separate log stack.
