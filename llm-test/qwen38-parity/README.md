# Qwen3.8-Flash-Next dual-Spark scaffold

**Status: prepared, not deployed.** The download Job is suspended and both
serving Deployments ship with `replicas: 0`. Nothing in this directory owns or
modifies the shared `ai-proxy` resources.

## Pinned provenance

- Recipe: [`MiaAI-Lab/Qwen3.8-Flash-Next-Dual-DGX-Sparks`](https://github.com/MiaAI-Lab/Qwen3.8-Flash-Next-Dual-DGX-Sparks/tree/d2ae28a9bedd6f063ee230d616bb320bd54a8f50)
- Recipe commit: `d2ae28a9bedd6f063ee230d616bb320bd54a8f50`
- Base image: `vllm/vllm-openai:qwen38-flash-next@sha256:fc120ece0a388cc0aa1caad4a9f1cd92113484ab7ec2fd0efadd62585be05bf8`
- Checkpoint: [`nvidia/Qwen3.8-Flash-Next-NVFP4`](https://huggingface.co/nvidia/Qwen3.8-Flash-Next-NVFP4/tree/fc694b54fb0174e0913e6adf86691ef85a4ead47)
- Checkpoint revision: `fc694b54fb0174e0913e6adf86691ef85a4ead47`
- 11 indexed weight shards, `132,680,249,378` bytes

The runtime patch tools in `upstream/` are copied from the pinned recipe. Their
upstream AGPL license and source marker are retained. The checkpoint carries
the NVIDIA Open Model License and underlying Qwen terms linked from its model
card. At pod initialization the pinned base image's own Python sources are
patched into `emptyDir` overlays; no mutable custom serving image and no
mutation of the canonical checkpoint are required. The complete Hugging Face
repository tree is mounted so snapshot symlinks can resolve into `blobs/`; a
symlink model view overlays only the checkpoint config aliases needed by MTP.

## Files

| File | Purpose |
|---|---|
| `05-qwen38-download.yaml` | Suspended, resumable, revision-pinned cache pull with indexed-shard and byte verification. |
| `kustomization.yaml` | Generates the patch ConfigMap and assembles serving resources. |
| `12-qwen38-parity.yaml` | Profile, patch preparation, warmup, and zero-replica TP2 head/worker Deployments. |
| `services.yaml` | Lane-specific ClusterIP Services only. |
| `upstream/` | Exact patch tools and license from the pinned recipe. |

## Deliberate K8s profile

The initial profile follows the recipe's agentic/native-context defaults:

- TP2 + expert parallel across chronometer and sextant;
- MTP with three speculative tokens;
- native 262,144 context, no YaRN;
- FP8 KV with the recipe's QSA patch;
- eight sequences, 8,192 batched tokens;
- BF16 GDN/Mamba state;
- API port 8000, the repository's exclusive dual-Spark lane slot;
- worker-first startup and head readiness gated on health plus 1/2/4/8 shape
  warmup.

The validated local CX7 settings are used: `172.16.5.55/.56`,
`enp1s0f1np1`, `mlx5_1:1`, GID 3, and RoCE v2. Master port 29921 is unique to
this scaffold.

## Preparation and eventual activation

Do not run these while another model is being actively evaluated unless the
storage/network impact is acceptable.

```bash
# Metadata only; Job remains suspended.
kubectl apply -f llm-test/qwen38-parity/05-qwen38-download.yaml

# Explicitly start the large download later.
kubectl patch job qwen38-dual-cache-pull-v1 -n llm-test \
  --type=merge -p '{"spec":{"suspend":false}}'

kubectl wait -n llm-test --for=condition=Complete \
  job/qwen38-dual-cache-pull-v1 --timeout=3h

# Creates Services/ConfigMaps and zero-replica Deployments.
kubectl apply -k llm-test/qwen38-parity

# Slot swap only after the existing Spark lane is fully stopped.
kubectl scale deploy/dsv41-exl3-head deploy/dsv41-exl3-worker \
  -n llm-test --replicas=0
kubectl scale deploy/qwen38-dual-worker -n llm-test --replicas=1
# Start rank 0 as soon as rank 1's init containers finish and its main process
# enters Running; rank 1 cannot become Ready before distributed rendezvous.
kubectl wait -n llm-test --for=jsonpath='{.status.phase}'=Running \
  pod -l app=qwen38-dual-worker --timeout=10m
kubectl scale deploy/qwen38-dual-head -n llm-test --replicas=1
kubectl rollout status deploy/qwen38-dual-worker -n llm-test --timeout=60m
kubectl rollout status deploy/qwen38-dual-head -n llm-test --timeout=60m
```

Before an eventual activation, re-check that the upstream tag/checkpoint have
not changed incompatibly, inspect the generated manifests, and verify port
29921 is free. Deployment and performance validation remain intentionally
outstanding.

## Astrolabe companion

`../30-qwen.yaml` is an independent single-node Strix Halo scaffold using the
Halogen Flash Server and a retained local NVMe PVC. It uses Service port 8000
to container port 8731 and can coexist with the dual-Spark lane because it does
not use host networking or the shared `ai-proxy`.
