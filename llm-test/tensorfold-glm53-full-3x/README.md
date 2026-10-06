# GLM-5.3 EXL3 full model (3x DGX Spark) — TensorFold lane, STAGED

**Status: STAGED. All three Deployments are checked in at `replicas: 0` and
nothing runs until you explicitly scale the ranks (order below).** The resident
TP2 TensorFold flash lane keeps both its Sparks, its port 8000, and the
`serving.homelab.io/alias=dgx-spark` route. This lane is prep work for the
full GLM-5.3 on all three Sparks — it must never fight the flash pair for GPUs,
ports, or traffic.

This is the Kubernetes port of MiaAI Lab's
[GLM-5.3-EXL3-3x-DGX-Sparks-TensorFold](https://github.com/MiaAI-Lab/GLM-5.3-EXL3-3x-DGX-Sparks-TensorFold)
recipe at `eb6414b488c3bc58605cad3dc96391c7584d6bec` (2026-10-05, the commit
that pinned the checkpoint revision). One rank per Spark over the 3-cable
ConnectX-7 triangle: 78-layer GLM-5.3 (MLA + DeepSeek sparse attention, 256
routed experts, MTP head), DSpark speculative drafting, copy drafts, RoCE
all-gathers, 4-bit dense weights, fp4 KV cache, context parallelism for the
499,712-token window, and the NVMe prompt cache (~5M prompt tokens).

## Immutable pins

| Item | Pin |
| --- | --- |
| Recipe | `MiaAI-Lab/GLM-5.3-EXL3-3x-DGX-Sparks-TensorFold @ eb6414b488c3bc58605cad3dc96391c7584d6bec` |
| Engine | TensorFold `v0.6.0` + 110 recipe patches (`tf.patches=4f3223245926`), FAST-built on the flash v1.4 image |
| Base image | `ghcr.io/miaai-lab/glm-5.3-flash-exl3-2x-dgx-sparks-tensorfold@sha256:14f15591eae5d6a540f09218d3852068962fe5381371bbfefe0e9194cd834529` (patches `5e01f1bb74d8`, verified arm64) |
| Lane image | `registry.taildeab2.ts.net/homelab/glm53-full-exl3:4f3223245926` — **pin the pushed digest into all image refs after the first build** |
| Checkpoint | `Mia-AiLab/GLM-5.3-EXL3-2.75bpw-TensorFold @ 2d747d0e30eca6e3fe37ba63c471cdf9172faa83` (137 shards, 292,737,786,480 bytes ≈ 273 GiB) |
| Drafter | `RedHatAI/GLM-5.3-speculator.dspark @ b374b95663447ea0e935151be4f3d6666e36e6d7` (2,499,134,874 bytes) |
| Served ID | `GLM-5.3-EXL3` |
| API | `glm53-full-head.llm-test.svc.cluster.local:8888/v1` (host network) |
| Rendezvous | port `29561`; scale worker2 → worker1 → head |

The patch hash was verified locally: `sha256(patches/0001..0141 + IMAGE_EXTRAS)`
== `4f3223245926`, matching the upstream release tag
`v0.6.0-4f3223245926` (image digest `sha256:1adb1f95...`). The checksum
inventories were generated from the immutable Hugging Face trees (LFS OIDs =
SHA-256; small metadata files hashed directly).

## Files

- `04-glm53-full-checksums.yaml` — immutable SHA-256 inventories: 144 verified
  files (137 shards + 7 metadata) for the checkpoint, 4 for the DSpark drafter.
- `05-glm53-full-download.yaml` — suspended Job pulling both repos into the
  shared `model-cache` PVC at 62.5 MB/s (≈ 80 min of pure transfer; resume-safe
  `.part` files). Verifies every byte against the inventories, checks the
  137-shard index set and exact weight bytes, then atomically writes
  `/models/.glm53-full-download-complete`. Both serving init gates require that
  exact receipt.
- `12-glm53-full-3x.yaml` — zero-replica rank 0/1/2 Deployments, headless
  rendezvous Services (29561), immutable receipt gate, TP=3 RoCE triangle
  discovery, head start-gate on both workers' logs, final VM-cache
  reclamation, and the recipe's long-context runtime.
- `14-glm53-full-image-build.yaml` — one-shot native-arm64 BuildKit Job that
  clones the pinned recipe, verifies revision + patch hash, and FAST-builds the
  lane image (42 full-model patches on the flash base) into the in-cluster
  registry.
- `services.yaml` — zero-endpoint internal API Service on port 8888 until rank
  0 is activated.

## Prerequisites (do these once, before anything else)

1. **Cabling**: a physical triangle — one CX7 cable from each Spark to each of
   the other two (3 cables total). The NixOS DGX Spark module must materialize
   `/var/lib/dgx-spark/rdma-fabric.json` on all three nodes with links to both
   peers (`peerControlAddress` per cable) and the control-plane address. The
   lane's fabric script fails closed if a node's inventory lacks a peer.
2. **Node capacity**: the shared `model-cache` RWX JuiceFS claim needs ~300 GiB
   free on top of the resident flash snapshots. Expand the PVC before the pull
   if needed (the flash lane expanded it 2→3 TiB for its 176 GiB pull; this
   lane's checkpoint is ~117 GiB larger).
3. **Device plugins**: every Spark advertises `nvidia.com/gpu: 1` and
   `rdma/hca_shared_devices: 1` (the `rdma-shared-device-plugin` Argo app is
   already cluster-wide; no change).
4. **PVC free check** before pulling:
   `kubectl df` is not available; check via a debug pod or the JuiceFS metrics.

## Image build (we build the containers ourselves)

```bash
kubectl apply -f llm-test/tensorfold-glm53-full-3x/14-glm53-full-image-build.yaml
kubectl logs -n llm-test -f job/glm53-full-image-build-eb6414b-v1
```

The Job pushes `local-registry.registry.svc.cluster.local:5000/homelab/glm53-full-exl3:4f3223245926`
and prints the digest. Then **pin the digest** into every image reference in
`12-glm53-full-3x.yaml` (tag `@sha256:...`), so a re-tag can never change what
the ranks run. The build needs an arm64 node with ~55 GiB of scratch; it
anti-affinities against the lane pods so it never lands on a serving Spark.

## Download lifecycle

The Job is suspended in Git so reconciliation never repeats a 293 GB pull:

```bash
kubectl apply -f llm-test/tensorfold-glm53-full-3x/04-glm53-full-checksums.yaml
kubectl apply -f llm-test/tensorfold-glm53-full-3x/05-glm53-full-download.yaml
kubectl patch job glm53-full-quant-pull-v1 -n llm-test --type=merge -p '{"spec":{"suspend":false}}'
kubectl logs -n llm-test -f job/glm53-full-quant-pull-v1
```

Completion is valid only when the Job is `Complete`, the log reports all 144 +
4 SHA-256 checks and the 137-shard / 292,737,786,480-byte totals, and the
receipt exists. The pull runs on `chronometer`, claims no GPU/HCA, and leaves
the resident flash snapshots untouched. Re-unsuspend to resume an interrupted
pull.

## Staging without cutover

```bash
kubectl apply --server-side -f llm-test/tensorfold-glm53-full-3x/12-glm53-full-3x.yaml
kubectl apply -f llm-test/tensorfold-glm53-full-3x/services.yaml
kubectl get deploy -n llm-test glm53-full-head glm53-full-worker1 glm53-full-worker2
kubectl get pods -n llm-test -l lane=glm53-full-3x   # must be empty
```

All ranks use the existing `llm-serving-critical` PriorityClass. Init order per
rank: stage-model-cache → checkpoint-check (cryptographic receipt) →
[head only: wait-for-ranks] → reclaim-vm-cache (≥ 110 GiB `MemAvailable`).

## Activation — only after explicit approval

This lane is an exclusive 3-GPU tenant. The flash pair must be down before any
rank starts (or there are neither enough Sparks nor free memory). TensorFold
TP=3 is not elastic: loss of any rank requires coordinated recreation of all
three (all down, worker2 → worker1 → head up).

1. Confirm the download receipt and zero lane replicas.
2. Stop the resident flash pair (head first, then worker) — or accept the
   downtime window.
3. Scale `glm53-full-worker2`, then `glm53-full-worker1`, then
   `glm53-full-head` to 1. Every rank's fabric discovery waits for all three
   rendezvous DNS names, so the last-scaled rank unblocks the other two; the
   head additionally gates on both workers' `rank N launching` logs.
4. Verify `/health` and `/v1/models` (served id `GLM-5.3-EXL3`) directly
   against `http://<head-node>:8888`, then one completion through
   `glm53-full-head.llm-test.svc.cluster.local:8888`.
5. For client cutover, point LiteLLM at the new endpoint or move
   `serving.homelab.io/alias=dgx-spark` to the qualified head template. Do not
   edit or restart LiteLLM for the move. Prove access to port 8888 from the
   real `ai-proxy` pod first (DEC-0023's proof obligation transfers to this
   lane's port; see DEC-0030).

If the RoCE all-gather (`TF_GLM_COMM=roce`) misbehaves on your cabling, set
`TF_GLM_COMM=nccl` in all three Deployments and restart the lane — the engine
falls back to NCCL collectives (upstream supports both; roce is ~10% faster on
small gathers).

## Rollback

Scale the lane head → worker1 → worker2 to 0, move the serving alias (if it
was moved) back to the flash head template, and start the flash pair worker →
head. The flash snapshots and manifests are untouched by this lane; the shared
PVC just holds the additional 293 GiB checkpoint. Delete
`/var/lib/llm-test/glm53-full-3x-cache` on the Sparks to reclaim kernel-cache
and prompt-cache disk (it is lane-scoped and safe to remove while replicas 0).

## Qualification notes (before trusting it daily)

- The recipe's own numbers (3 Sparks, one request at a time, defaults):
  31.3 tok/s prose / 41.7 tok/s code decode, ~600 tok/s prefill to 32k, 545
  tok/s at 94k — TTFT 5 ms on cache, minutes on a cold 500k prompt.
- `tools/exact.py` from the recipe repo: drafted replies equal serial ones and
  concurrent requests match solo replies — worth a run after first boot.
- The prompt cache needs ~6.7 GB per Spark for a full 500k-token conversation
  and keeps ~5.1M prompt tokens at the default 64 GiB budget
  (`TF_GLM_DISK_CACHE_GIB`); the least-recently-used states evict first.
