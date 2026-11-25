# GLM-5.3-Flash 1104 B-pair — parallel validation lane on the new cache tier

Clone of `../glm53-flash-1104` (recipe 1104, d4226a1 engine) built to run
**simultaneously** with the live A-pair while pointing at the NEW encrypted
cache tier (`model-cache-ephemeral-v2` / juicefs-cache-sc). Purpose: validate
the new volume under real serving load without touching live traffic.

## What differs from the A-pair

| Aspect | A-pair (live) | B-pair (this lane) |
|---|---|---|
| PVC | `model-cache` (old tier) | `model-cache-ephemeral-v2` (new encrypted tier) |
| Deployments | `glm53-flash-1104-{head,worker}` | `glm53-flash-1104-b-{head,worker}` |
| Serve/qual port | 8000 | **8100** (hostNetwork — ports are node-scoped; 8000 would collide if both pairs landed on one node) |
| NCCL bootstrap/watch | 29583/29584 | **29593/29594** (incl. `NCCL_COMM_ID`) |
| Context auto-fit TSV | `glm53-1104-context.tsv` | `glm53-1104-b-context.tsv` (min-wins logic assumes exactly 2 ranks per file — files MUST NOT be shared) |
| Rank-state hostPath | `/var/lib/llm-test/glm53-flash-1104-state` | `/var/lib/llm-test/glm53-flash-1104-b-state` |
| Serving alias | `dgx-spark` | `dgx-spark-b` (service `dgx-spark-b-backend`) |
| ManagedWorkload priority | 90 | **80** (B can never preempt A) |
| Placement | bestRoute | bestRoute in CR, but **hard TEMP-PINs** (below) |

Image is identical (pinned): `tensorfold-glm53-flash-1104:ef2e6847aa4a-py3-v1@sha256:cc2af44e04d6a2c73a710f14df9ed58a15a4fe7d67ecbdd575f1018e98ddd04e`.

## Placement (post DEC-0063 multi-slot capacity)

Pool `dgx-spark` capacity is 4 spark units; A and B each demand 2 (default:
member replica count), so both are admitted and co-resident. Placement is
Conductor-owned (`bestRoute`): occupancy-aware adjacent pairing gives each
lane a disjoint ring-adjacent pair (A on its current nodes, B on the free
pair) without any manifest pins. Earlier TEMP-PINs were removed — they were
overwritten by Conductor placement at runtime anyway.

## Conversation persistence## Conversation persistence + KV sharding (validation features)

The B-pair also validates two recipe features the A-pair doesn't run:

- **`LEARN_GIB=30` / `LEARN_MIN_FREE_GIB=15`** (recipe patch 0113): prompt
  states written to disk (`CACHE_DIR/learn`) so conversations resume after
  eviction or restart — measured upstream at 102.5k tokens in 1.8 s vs 58.4 s
  cold. Store is a **40 GiB emptyDir** on the pod (node-local NVMe, k8s-managed
  cleanup on pod removal). The engine's own `LEARN_MIN_FREE_GIB=15` is the
  rolling limit — nothing is written below 15 GiB free. Restart-of-pod loses
  the store (emptyDir); move to the cache ring via subPath if cross-restart
  persistence is wanted after validation.
- **`KV_SHARD=1`** (recipe patch 0114): each stream's latent rows stay on one
  Spark — roughly 2x token capacity at a 1-4% decode cost. Requires KV=fp8 +
  KV_PAGES=on + DFlash2 (defaults already set). TP=2 only, so `start-tp4.sh`
  semantics don't apply here.

If either misbehaves during validation, revert by setting the env to the
A-pair defaults (`LEARN_GIB=0`, `KV_SHARD=0`) in one reviewed commit — no
volume changes needed.
