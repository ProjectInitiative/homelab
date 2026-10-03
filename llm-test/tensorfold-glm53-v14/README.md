# TensorFold GLM-5.3-Flash v1.4 recipe lane (2x DGX Spark) — STAGED

**Status: DOWNLOAD IN PROGRESS; DO NOT ACTIVATE.** The active v1.2 pair and
LiteLLM route are intentionally untouched. Both v1.4 Deployments are checked in
and applied at zero replicas. Cutover requires explicit operator approval after
the immutable checkpoint download and verification complete.

This is the Kubernetes port of MiaAI Lab's
[GLM-5.3-Flash EXL3 TensorFold recipe](https://github.com/MiaAI-Lab/GLM-5.3-Flash-EXL3-2x-DGX-Sparks-TensorFold)
at the untagged v1.4 release-marker commit
`fcc33211887c79e11654faed717e892d9e1449cd` (2026-10-03). Do not follow current
`main`: it already contains unreleased v1.5 changes.

## What changes from v1.2

- TensorFold `v0.5.0` -> `v0.6.0`; 53 -> 68 recipe patches.
- Runtime image -> `v0.6.0-5e01f1bb74d8`, pinned by digest.
- Checkpoint -> MiaAI's TensorFold-calibrated EXL3 quant, 83 shards / ~176 GB.
- Default reply budget becomes 32,768 when clients omit `max_tokens`.
- `TF_GLM_MTP=auto` avoids loading the checkpoint MTP head with DFlash2.
- Kept-state behavior follows v1.4: `MULTI_LONE=0`, 32 cache entries, earlier
  reasoning retained, smooth streaming, and sliced concurrent prompt fills.
- The TP2 topology, 1,048,576-token context, FP8 KV, q4 dense path, four
  streams, DFlash2 pin, RoCE adaptation, port 8000, and memory profile remain.

The new checkpoint is the only large download. DFlash2 remains pinned at
`bf582e4eacc1810f76656d1811693ff6c6737d2a` and is already cached.

## Immutable pins

| Item | Pin |
|---|---|
| Recipe | `MiaAI-Lab/GLM-5.3-Flash-EXL3-2x-DGX-Sparks-TensorFold @ fcc33211887c79e11654faed717e892d9e1449cd` |
| Engine | TensorFold `v0.6.0` + 68 recipe patches (`tf.patches=5e01f1bb74d8`) |
| Image | `ghcr.io/miaai-lab/glm-5.3-flash-exl3-2x-dgx-sparks-tensorfold@sha256:14f15591eae5d6a540f09218d3852068962fe5381371bbfefe0e9194cd834529` |
| Checkpoint | `Mia-AiLab/GLM-5.3-Flash-EXL3-4bpw-TensorFold @ 078455ffe6472f9a52fbc1139f58b9db2881b25c` |
| Drafter | `incoai/GLM-5.3-Flash-DFlash2 @ bf582e4eacc1810f76656d1811693ff6c6737d2a` |
| Served ID | `GLM-5.3-Flash-EXL3` |
| API | `tensorfold-v14-head.llm-test.svc.cluster.local:8000/v1` |
| Rendezvous | port `29551`, worker first then head |

The image manifest was independently verified as Linux arm64; its compressed
layers total 11,372,502,373 bytes and carry `tf.patches=5e01f1bb74d8`.

## Files

- `04-tensorfold-v14-checksums.yaml` — immutable SHA-256 inventory for all 83
  shards plus eight runtime metadata files at the pinned Hugging Face revision.
- `05-tensorfold-v14-download.yaml` — suspended-in-Git Job using the pinned
  puller-v5 image's resumable `hf`/Xet client for the new checkpoint. It verifies all 91 file digests, the exact
  83-shard index set, and 175,642,267,944 shard bytes before atomically writing
  `/models/.tensorfold-v14-quant-download-complete`. It deletes nothing.
- `12-tensorfold-v14-glm53.yaml` — zero-replica TP2 lane, immutable cache gate,
  RoCE discovery, rank-order gate, final VM-cache reclamation, and v1.4 runtime.
- `services.yaml` — zero-endpoint internal API Service until rank 0 is activated.

The shared `model-cache` RWX JuiceFS claim was expanded online from 2 TiB to
3 TiB before the pull because only ~140 GiB remained. The active v1.2 snapshot
is retained as rollback material.

## Download lifecycle

The Job is kept suspended in Git so reconciliation does not repeat a 176 GB
pull. To run it deliberately:

```bash
kubectl apply -f llm-test/tensorfold-glm53-v14/04-tensorfold-v14-checksums.yaml
kubectl apply -f llm-test/tensorfold-glm53-v14/05-tensorfold-v14-download.yaml
kubectl patch job tensorfold-v14-quant-pull-v1 -n llm-test \
  --type=merge -p '{"spec":{"suspend":false}}'
kubectl logs -n llm-test -f job/tensorfold-v14-quant-pull-v1
```

Completion is valid only when the Job is `Complete`, its log reports all 91
SHA-256 checks plus 83 shards / 175,642,267,944 bytes, and the cryptographic
receipt exists. Both serving init gates require that exact receipt. The pull runs on chronometer, requests 500m CPU / 1 GiB RAM plus a 220 GiB
ephemeral-storage reservation, claims no GPU/HCA, and leaves the active Sparks
alone. Hugging Face locks/Xet state stay in the dedicated node-local
`/var/lib/llm-test/tensorfold-v14-staging` directory; only the completed
snapshot is copied to JuiceFS (eight files in parallel), then the shared copy is
SHA-256 verified. The local staging directory is removed after success. Xet
chooses its own transfer concurrency; site-link and final JuiceFS copy traffic
remain observable.

## Staging without cutover

```bash
kubectl apply --server-side -f llm-test/tensorfold-glm53-v14/12-tensorfold-v14-glm53.yaml
kubectl apply -f llm-test/tensorfold-glm53-v14/services.yaml
kubectl get deploy -n llm-test tensorfold-v14-head tensorfold-v14-worker
kubectl get pods -n llm-test -l lane=tensorfold-v14   # must be empty
```

Both ranks use the existing `llm-serving-critical` PriorityClass. CSI, storage,
device-plugin, kubevirt-critical, and Kubernetes system pods remain above them.
Every init container forces `NVIDIA_DRIVER_CAPABILITIES=compute,utility`.

## Cutover — only after explicit approval

The v1.2 and v1.4 lanes share both GPUs, host port 8000, and rendezvous port;
they must never run together.

1. Confirm download marker and zero v1.4 replicas.
2. Stop v1.2 **head**, then **worker**, and wait for both pods to disappear.
3. Start v1.4 **worker**, then **head**.
4. Both final privileged cache gates must reclaim VM cache and pass at least
   110 GiB `MemAvailable`; recreate pods after a failed main-container start.
5. Validate direct `/health`, `/v1/models`, and completion from `ai-proxy`.
6. Only then change LiteLLM `dgx-spark` from `tensorfold-v12-head` to
   `tensorfold-v14-head`, restart the proxy, and run a public completion.

Do not treat rank-0 readiness alone as pair health. TensorFold TP2 is not
elastic: loss/recreation of either rank requires coordinated pair recreation
(head down, worker down, worker up, head up; RISK-0018).

## Rollback

Keep the v1.2 manifests and TR3 snapshot. To roll back, stop v1.4 head then
worker, start v1.2 worker then head, validate directly, and restore the LiteLLM
route. Never rely on an isolated replacement rank joining a surviving NCCL
session.
