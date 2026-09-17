# tonyd2wild GLM-5.3-Flash NVFP4/DFlash2 — build-only scaffold

This directory records the Kubernetes scaffold for
[tonyd2wild/GLM-5.3-Flash-NVFP4-DFlash2-2x-DGX-Spark](https://github.com/tonyd2wild/GLM-5.3-Flash-NVFP4-DFlash2-2x-DGX-Spark).
It is **not enabled**: the cache Job has `suspend: true` and both rank
Deployments have `replicas: 0`. Do not unsuspend or scale this lane as part of
normal manifest validation.

## Files

- `05-tonyd2wild-download.yaml` — suspended cache pull for both NVFP4 variants
  and the separate DFlash2 drafter. It does not delete existing caches.
- `12-tonyd2wild-glm53.yaml` — head/worker Deployment skeleton, both at zero
  replicas, using the upstream image and two-node vLLM multiprocessing shape.

## Verified upstream inputs

| Input | Repository / pin |
|---|---|
| Upstream recipe snapshot | `tonyd2wild/GLM-5.3-Flash-NVFP4-DFlash2-2x-DGX-Spark` @ `9acb1fbbf6c1a9924651fd8694aa197a266cd6b6` |
| Default NVFP4 | `RedHatAI/GLM-5.3-Flash-NVFP4` @ `c245560b6d7e62c329cd3042343b358a4279affd` |
| Uncensored NVFP4 | `drowzeys/keys-GLM-5.3-Flash-NVFP4-ablit-l15-45-anchorstock` @ `80b6d18d77e3020f2384597081d405f19893f101` |
| DFlash2 drafter | `incoai/GLM-5.3-Flash-DFlash2` @ `dc77ff1c99eeb2df044ee3d4f0094eb033fee410` |
| Runtime image | `ghcr.io/tonyd2wild/vllm-glm53-flash:sm121-v11-dflash2` @ `sha256:4def0ef644cb2e9814136dcffd5e385e21bc594f48f3b292234051904abe85a6` |
| Cache puller | `registry.taildeab2.ts.net/homelab/glm53-cache-puller:v5` @ `sha256:4ac2072503bd68a509e556c1e1970ba498c4c7d632205879be623126b53e49ec` |

The two model repositories were confirmed through the Hugging Face API. The
named `tonyd2wild/...` Hugging Face repository from some launcher discussions
is not used: its API is private or unavailable (HTTP 401), so no unverified
repository or URL is invented here.

## Before any future activation

1. Confirm PVC capacity for both ~198 GB NVFP4 trees plus the DFlash2 tree.
2. Scale every other host-network lane using port `8000` to zero. This lane is an
   exclusive slot: start its worker before its head, and stop its head before its
   worker.
3. If the uncensored pull is gated, create `llm-test/huggingface` with `HF_TOKEN`.
4. Supply the upstream SM121 `sparse_attn_indexer_kpool.py` patch to the image
   at `/usr/local/lib/python3.12/dist-packages/vllm/model_executor/layers/`;
   the Deployment init check fails closed until that file path is present. Verify
   its contents are the patched upstream file before scaling; the patch is
   deliberately not copied from another lane.
5. Replace the documented upstream `192.168.192.x` addresses and interface
   names with the actual two-node RoCE fabric values for this cluster. The
   scaffold defaults mirror the upstream launcher, not a claim about local
   network topology.
6. Run a target-specific vLLM load smoke test. The inspected model revisions
   provide `chat_template.jinja`; the launcher mentions `chat_template_mm.jinja`,
   so the manifest falls back to the available template but multimodal behavior
   remains unqualified.

To prepare cache only after explicit approval:

```bash
kubectl apply -f llm-test/tonyd2wild-glm53/05-tonyd2wild-download.yaml
kubectl patch job tonyd2wild-glm53-cache-pull-v1 -n llm-test \
  --type=merge -p '{"spec":{"suspend":false}}'
```

No apply, patch, scale, or image build is performed by this change.
