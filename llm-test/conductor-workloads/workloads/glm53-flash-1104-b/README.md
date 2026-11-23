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

## TEMP-PIN placement (validation window)

- head pinned to node `chronometer`, worker pinned to `sextant`
  (`kubernetes.io/hostname` nodeSelectors, marked `TEMP-PIN` in
  `02-serving.yaml`). Guarantees disjoint nodes from the A-pair during
  validation and exercises the 4-node cache ring.

## Cutover plan (after A-pair teardown)

1. A-pair stands down (user-authorized; cutover.sh/revert.sh in the A lane).
2. Volume rename dance: `model-cache-ephemeral-v2` → `model-cache-ephemeral`;
   update per-PVC `matchName` mountPodPatch selectors in `clusters/mc.yaml`.
3. **In one reviewed commit**: remove both `TEMP-PIN` nodeSelectors from
   `02-serving.yaml` (fall back to the CR's `bestRoute` placement) and, if
   desired, move serve port 8100 → 8000 back to the canonical shape.
4. After B reaches steady state on `bestRoute`, verify ring spread: all 4 DGX
   nodes (chronometer, sextant, octant, astrolabe) mount
   `model-cache-ephemeral-v2` — check juicefs mount pods per node:
   `kubectl get pods -A -o wide | grep juicefs` and confirm one mount pod per
   node holding the ring PVC.
