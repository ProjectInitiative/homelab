# GLM-5.3-Flash DGX Sparks — TensorFold native recipe 1104 (STAGED)

This is a Kubernetes/Conductor port of [MiaAI-Lab/GLM-5.3-Flash-DGX-Sparks-1104](https://github.com/MiaAI-Lab/GLM-5.3-Flash-DGX-Sparks-1104), pinned at recipe commit `94b72f557268f2ea46852ac03c81119d21f3611e` (upstream `main`). It builds the recipe's TensorFold native Zig/CUDA engine (`f350cd3ea253a042e205746928271f9d8f71a82d`) plus its 105 patches for GB10 `sm_121`. The vision template is vendored from the pinned recipe. The commit move from `3066a3fe` is launch-only (reasoning-effort default, worker-login and TP4 script removals); no `patches/engine/` or `docker/Dockerfile` bytes changed, so the digest-pinned serving image already contains the current engine — rerunning the build Job is provenance-only and produces the same tag.

**Staged; second cutover rolled back through GitOps.** The first diagnosable retry proved both GLM ranks exited before TensorFold launch: chronometer saw `MemAvailable` around 22.3 GiB and sextant around 23.3 GiB against the 100-GiB gate. A review against the recipe's verified `start.sh` path found three launch gaps the previous manifest lacked, now closed in `02-serving.yaml`:

1. **No memory reclamation before the gate.** Upstream refuses to start under `MIN_AVAIL_GIB=100`; the rank started while v14's memory/page cache was still being released and exited 1. Both GLM Deployments now have a bounded privileged cache-reclamation init container matching v14, followed by the rank gate (`GLM_MIN_AVAIL_GIB=100`).
2. **No context auto-fit.** Upstream defaults `CONTEXT=auto`: start at 1,048,576 and, when a rank refuses with its memory figures, restart at the window the refusal allows (`fits: ... --context T`). The manifest hard-coded 1M with no retry. The launcher now parses the refusal, records the fitted window in `/lane-state/glm53-1104-context.tsv` on the shared `model-cache` PVC (min wins, so both ranks' fingerprints agree), and retries smaller — the same convergence `start.sh` gets from its log scraping, coordinated through the PVC instead of both ranks' local state dirs.
3. **Logs were not preserved.** Rank output now appends to the node-local `/var/lib/llm-test/glm53-flash-1104-state/logs/` hostPath, so a terminated container's refusal text survives pod recreation.

Minor parity env (`TF_GLM_W8A8=0`, `TF_GLM_CE_EXCHANGE=0`) and the newer recipe's `--reasoning-effort xhigh` default were added at the same time. The synthetic CUDA checks ran clean for the reference path (`tf-cuda-test glm-ref` passed on sextant); the synthetic mixed-bit `glm-exl3` long-prompt case fails at `tf_exl3_group` on both Sparks (128 KiB dynamic shared request vs the pinned source's 64 KiB registration) — a real upstream kernel defect candidate for long prompts, but not established as the startup-exit cause. Initial transport remains NCCL-only (`TF_ROCE=0`); custom RoCE remains unqualified (OQ-0050).

Image-build v1 failed before BuildKit because the rootless image has no `/bin/bash`; v2 failed loading `docker/Dockerfile` because its local source was not declared. Neither attempt mounted `model-cache` or published an image. v3 succeeded; the failed Job records are retained for logs and expire by TTL.

**Image-build v4 for the newer recipe pin (image provenance only).** `07-image-build-d4226a1.yaml` builds upstream commit `d4226a1bd62a7d264f116fc4736106a037090365`, the first pin whose build inputs differ from the image behind the v3 tag: six engine patches (0107-0112) and a `video` stage in `docker/Dockerfile`. Upstream's `scripts/prepare.sh` `PATCHES_HASH` therefore moves from `74e19a63a9a5` to `ef2e6847aa4a` (the same procedure over `git archive 94b72f5` reproduces `74e19a63a9a5`, so the method matches the v3 image), and the Job tags `local-registry.registry.svc.cluster.local:5000/homelab/tensorfold-glm53-flash-1104:ef2e6847aa4a`. The build container recomputes that hash from the fetched tree using the same pins it passes to BuildKit, asserts it equals `ef2e6847aa4a`, fails closed before pushing on a mismatch, and never hashes a stale literal. The Job is PVC-free like v3, keeps the arm64/rootless-BuildKit security shape, and is deliberately **not** in `kustomization.yaml` because this lane syncs with automated selfHeal; its `argocd.argoproj.io/hook: Skip` annotation keeps Argo from executing it even if it is wired in later. It reuses the lane's immutable `glm53-flash-1104-buildkit-config` ConfigMap. The completed v3 Job and the `74e19a63a9a5` tag are untouched.

Operator trigger and immutable-digest check (one line each; re-running an existing Job is a no-op, so `kubectl -n llm-test delete job glm53-flash-1104-image-build-d4226a1` first if it must run again):

```bash
kubectl apply -f llm-test/glm53-flash-spark-1104/07-image-build-d4226a1.yaml
kubectl -n llm-test logs job/glm53-flash-1104-image-build-d4226a1 | sed -nE 's/.*exporting manifest( list)? sha256:([0-9a-f]{64}).*/sha256:\2/p' | tail -n 1
```

The Job publishes a tag; the new Python3 derivative is staged separately below. Neither build changes `02-serving.yaml`: the lane keeps serving the digest-pinned `74e19a63a9a5-py3-v2` image.

**Python3 derivative for recipe d4226a1.** Native Job `glm53-flash-1104-image-build-d4226a1` completed in 8m52s; BuildKit pushed `ef2e6847aa4a@sha256:8ec389d675f4fbe47754e948652e3999cf2aa1cf9f59a3b3973566e501db798b`, independently matched by a registry HEAD request. `docker/Dockerfile.runtime-d4226a1` pins that digest. `09-runtime-dockerfile-config-d4226a1.yaml` carries its exact bytes as an immutable ConfigMap, and the suspended `08-runtime-image-python3-build-d4226a1.yaml` Job checks the pinned `FROM` format before BuildKit. Both are omitted from `kustomization.yaml`; neither touches a GPU or the model-cache PVC. The existing v2 derivative and served image remain unchanged.

Operator commands if the derivative must be recreated manually (run each independently; never reapply a different digest to the immutable ConfigMap):

```bash
kubectl create -f llm-test/glm53-flash-spark-1104/09-runtime-dockerfile-config-d4226a1.yaml
kubectl create -f llm-test/glm53-flash-spark-1104/08-runtime-image-python3-build-d4226a1.yaml
kubectl -n llm-test patch job glm53-flash-1104-image-py3-d4226a1 --type=merge -p '{"spec":{"suspend":false}}'
kubectl -n llm-test wait --for=condition=complete job/glm53-flash-1104-image-py3-d4226a1 --timeout=1800s
```

Capture the derivative manifest digest, compare it independently with the registry result, and record `ef2e6847aa4a-py3-v1@sha256:<verified-digest>` for a separately reviewed serving update:

```bash
kubectl -n llm-test logs job/glm53-flash-1104-image-py3-d4226a1 | sed -nE 's/.*exporting manifest( list)? sha256:([0-9a-f]{64}).*/sha256:\2/p' | tail -n 1
crane digest registry.taildeab2.ts.net/homelab/tensorfold-glm53-flash-1104:ef2e6847aa4a-py3-v1
```

The ConfigMap is immutable; if a new base digest is needed, preserve the old build record and use a new ConfigMap/Job name. No build result by itself authorizes switching serving.

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
- Fabric discovery is performed by each serving rank on its scheduled node from the node-local inventory; the launcher validates both rails and HCA/GID selection before starting TensorFold.
- The live smoke Job was removed from the active Kustomization after the retry failed; it is not a serving or cache resource.
- `02-serving.yaml` mirrors the current TensorFold v14 two-rank Kubernetes shape: host networking/IPC, `nvidia-rdma`, node capability scheduling and anti-affinity. Worker rank 1 starts first; its launcher waits for the head rendezvous, so the worker uses `DeploymentAvailable` as the Conductor gate and then Conductor starts head rank 0. The launcher replicates `start.sh`'s memory gate, rank-log preservation and context auto-fit (see the status section above). The initial serving window uses NCCL-only; head health gates the stable route.
- `03-managed-workload.yaml` uses `RecreateTogether` so a rank failure recreates the pair. It is `Standby` pending root-cause of the serving-rank startup failure; its head carries the stable `dgx-spark` alias.

The serving manifest reuses the existing `tensorfold-v14-rdma-fabric` ConfigMap and `/var/lib/dgx-spark/rdma-fabric.json` host inventory. NCCL bootstrap is placed on the shared control-plane address; NCCL/engine data traffic is selected from the node-local RoCE inventory. This is the Kubernetes adaptation to validate; upstream's launcher discovers its direct-link address through SSH.

## Cutover / revert scripts

**Operator-only recovery; not authorization to activate 1104.** Current expected pre-recovery state is v14 `Standby`, 1104 `Standby`, both lanes at `0/0`, and no `dgx-spark-backend` endpoint. Before any recovery, use an identity authorized to read both ManagedWorkload spec and Conductor status and patch ManagedWorkloads. The agent/MCP identity cannot read Conductor status; `revert.sh` deliberately exits before writes if either intent is unreadable/missing (including RBAC denial). No concurrent cutover/activation is allowed during this recovery. Cross-resource Conductor patches are not atomic; the script rechecks 1104 after v14 activation and throughout readiness/endpoint checks, but cannot eliminate the interval between checks. If it detects a race it stops without corrective patches; inspect state and have an authorized operator decide next steps. Do not work around RBAC or directly `kubectl scale` either Deployment.

One-line read-only preflight (each expected intent field should agree; both Deployments should be 0/0 and stable API should have no endpoints):

```bash
kubectl get managedworkload glm53-flash-1104 tensorfold-v14 -n llm-test -o custom-columns=NAME:.metadata.name,DESIRED:.spec.desiredState,EFFECTIVE:.status.effectiveIntent; kubectl get deploy glm53-flash-1104-worker glm53-flash-1104-head tensorfold-v14-worker tensorfold-v14-head -n llm-test; kubectl get endpoints dgx-spark-backend -n llm-test
```

Before running recovery, verify source configuration in `clusters/mc.yaml`: the final `model-cache` PVC-specific CSI patch is last, pins `juicefs-gcache-csi:c86f272-arm64@sha256:839c41f475f4b82392b7b52c920d9546ba3fbc5b0d1d6286008dfffe0d076f5e`, and includes `cache-group=dgx-model-cache`, `group-listen=:13910`, and `group-advertise=auto-c7`. That source check does not prove fresh-node mounts. After v14 boots, confirm its newly created mount pods use the expected image/flags and ring membership before claiming fresh mounts are proven. Do not launch a full model warmup, change storage/cache configuration, delete/recreate mounts, or perform cache mutation; v14's init container intentionally reclaims page cache before its 110-GiB availability gate.

- `./cutover.sh` is a separate explicitly authorized activation flow; it stops v14, brings 1104 up, then checks the API and a completion smoke. It does not revert automatically.
- `./revert.sh` requests 1104 `Standby`, verifies both desired/effective intent fields, then requires **each** 1104 Deployment's `spec.replicas=0` and no matching Pods (including terminating Pods) before it requests v14 `Resident`. It rechecks 1104 after v14 activation and during rank/endpoint checks; any change/read error stops without automatic corrective patches. It waits for v14 worker then head, requires distinct nodes, and verifies the stable Service's sole endpoint IP equals the Ready v14 head Pod IP with repeated health checks. It ends **PROVISIONAL** and requires an interactive `CONFIRM_RING_AND_API_SMOKE` only after the separate CSI/ring and API smoke checks below; non-interactive use cannot report completion. `REVERT_TIMEOUT` (default 2700s); `INTENT_TIMEOUT` (default 120s); `DOWN_TIMEOUT` (default 600s).

Run only after preflight, with authorized access:

```bash
./revert.sh
```

Before entering the confirmation token, identify the Ready rank Pods/nodes and CSI mount Pods on those same nodes. Rank query (the script also verifies exactly one Running/Ready Pod per rank and the head Pod IP against the stable Service endpoint):

```bash
kubectl get pods -n llm-test -l 'app in (tensorfold-v14-head,tensorfold-v14-worker)' -o wide
```

For each rank node, list its Pods and inspect the corresponding JuiceFS CSI mount Pod (replace node/namespace/name with observed values; do not restart/delete it):

```bash
kubectl get pods -A -o wide --field-selector spec.nodeName=<rank-node>; kubectl describe pod -n <mount-pod-namespace> <model-cache-mount-pod>; kubectl logs -n <mount-pod-namespace> <model-cache-mount-pod> --all-containers --tail=200
```

Confirm the fresh mount Pod uses digest `sha256:839c41f475f4b82392b7b52c920d9546ba3fbc5b0d1d6286008dfffe0d076f5e`, and its effective argv/config has `/mnt/pool/juicefs-ring`, `cache-group=dgx-model-cache`, `group-listen=:13910`, `group-advertise=auto-c7`, and the remaining expected options from the final `model-cache` CSI patch in `clusters/mc.yaml`. Confirm ring membership/advertise from its runtime logs; an image/config match alone does not prove membership. These are operator checks because CSI mount Pod naming/representation is runtime-generated and is not declared as a stable repository API. If mount identity/options or membership cannot be established, do not type the confirmation token: the recovery remains PROVISIONAL and is not complete.

Then run an authorized direct smoke against the endpoint reported by the script: `/health`, `/v1/models`, and one short completion. Only after both CSI and smoke checks pass enter `CONFIRM_RING_AND_API_SMOKE`. Abort/recovery check (read-only): rerun the preflight line above and inspect rank events/logs. On any failure, do not scale manually, warm caches, or mutate CSI/cache; leave observed intents as-is and have an authorized operator decide next steps. A failure after v14 was requested does not automatically change either intent. Rank refusal logs are preserved at `/var/lib/llm-test/glm53-flash-1104-state/logs/` on rank nodes.

## Activation gates / rollback

1. Keep recipe 1104 `Standby` until an exclusive window: set v14 `Standby`, let its memory release, then activate 1104 and watch `/state/logs/rank*.log` on each rank node — the memory gate, fit file and preserved logs make the next failure diagnosable. Restore v14 `Resident` if the pair does not come up.
2. The serving mounts of `model-cache` remain read-only; the only lane write is the small `glm53-1104-context.tsv` fit file via the dedicated `/lane-state` mount of the same PVC (the same place the pull receipt lives).
3. A retry must remain NCCL-only (`TF_ROCE=0`); do not enable custom RoCE until OQ-0050's rank/GID and cross-rank qualification passes.
4. A future smoke must wait for the recipe API endpoint and then verify `/health`, `/v1/models`, a short completion, both ranks, memory reserve, and the stable Service endpoint after cold load.
5. Roll back through GitOps by setting recipe 1104 `Standby` and v14 `Resident`; never run both TP2 workloads simultaneously.

The image build did not mount or write `model-cache`. The downloader added only the pinned snapshots; serving mounts the PVC read-only. Git manifests keep rank replicas at zero while Conductor owns runtime scale. The stable API Service remains on port 8000 and follows the head's `serving.homelab.io/alias=dgx-spark` label.

## Source and licensing

The pinned recipe is Apache-2.0; its upstream `LICENSE`, `NOTICE.md`, and `CREDITS.md` apply. The vendored vision template is from that exact commit. TensorFold, Hugging Face model weights, and DFlash2 retain their own licenses/terms. See the upstream README and notices before activation.
