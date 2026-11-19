# glm53-exlr8-k4 — GLM-5.3 exlr8 bit400 (K4) cache preload (STAGED, pull only)

Cache-only staged lane for the KindlingAI **gr8** engine serving
GLM-5.3 (744B MoE) on DGX Sparks. This phase downloads the pinned checkpoint
into the shared `model-cache` PVC and verifies it. **No serving workload is
created; no ManagedWorkload is registered** — the serving/k8s-shape design
pass is a separate, later phase (see "Deferred" below).

## Model + recipe decision

- Checkpoint: `kindlingai/glm-5.3-exlr8-k2-k3-k4` — GLM-5.3 in the **exlr8 v2
  format**: every routed expert stored at three widths (K2 ≈2-bit, K3 ≈3-bit,
  K4 ≈4-bit), width profile chosen at load time via a manifest. Tag `v0.7`,
  weight set `3d1a293399f0077e27acd18609ee67f33f8e3f8b5963a7c4b42b7dc16ecd1d98`.
- Engine: [kindlingai/gr8](https://github.com/kindlingai/gr8) — the exlr8-native
  engine for GB10-class devices, serving at TP=3/4 (up to 3–6 boxes).
- Recipe: [`glm-5.3-exlr8-k4-4x-spark`](https://github.com/kindlingai/glm-5.3-exlr8-k4-4x-spark)
  (TP=4, four Sparks). **`glm-5.3-flash-exlr8-2x-spark` is a different model**
  (GLM-5.3-Flash) and does not apply.
- Target profile: **`bit400`** — the release's widest/highest-precision profile
  (operator choice 2026-11-18: "keep the highest precision one"): every routed
  expert at K4, with the MTP layer 78 at K3 (the only width the release stores
  for it). Manifest `manifests/exlr8-manifest-bit400.json`. Card KL vs BF16 on
  model-written text: 0.038 mean / 0.0057 median — the best in the release, a
  hair better than `bit387` (0.0385 / 0.0058, the 4x-spark recipe's default)
  at the cost of 3 GB more per box (92 vs 89 GB experts/box at TP4). The gr8
  engine is validated serving bit400 at TP4 (model card "Known results").
  Lower profiles (bit387/bit300/…) can be enabled later by extending the
  pull include filter — the puller resumes incrementally, no re-download of
  present files.

### KL table (model-written text, mean/median — from the HF card, v0.7)

| profile | size | KL mean/median |
|---|---|---|
| bit200 | 199 GB | 0.248 / 0.0440 |
| bit271 | 263 GB | 0.095 / 0.0142 |
| bit300 | 290 GB | 0.071 / 0.0106 |
| bit322 | 310 GB | 0.058 / 0.0088 |
| **bit387** | **368 GB** | **0.039 / 0.0058** |
| bit400 | 380 GB | 0.038 / 0.0057 |

Full table on the [model card](https://huggingface.co/kindlingai/glm-5.3-exlr8-k2-k3-k4#width-profiles).
Comparison caveat: this KL test is harsher than the short panels other GLM-5.3
quant cards use; only compare within it.

## Pull plan

We pull the **bit400 file set** (~357 GiB of the 782 GiB repo): all K4 experts
(339 GiB), the K3 MTP layer (~2 GiB), plus dense/vocab, all manifests, all
per-layer expert indexes, the TP4 index slices and the hash files (~16 GiB,
needed by any profile). K2 and mid-layer K3 are skipped — if a lower profile
is wanted later, extend the filter and re-run; the puller downloads only the
missing files in place.

Pin: `kindlingai/glm-5.3-exlr8-k2-k3-k4@9e25c28a2e8808d8b2599d780521fd6af24e7558`

Estimated on-juicefs footprint: ~357 GiB. `model-cache` PVC is 3 Ti.

The pull uses the **generic puller**
(`homelab/model-cache-puller:v7` — see `llm-test/puller/README.md`; the old
`glm53-cache-puller` name is a deprecated alias of the same tool) with the
include-filter spec:

```
config.json|generation_config.json|tokenizer*.json|chat_template.jinja|manifests/*|dense/*|index-slices/tp4/*|experts/*.index.safetensors|experts/*.k3.safetensors|experts/*.k4.safetensors|hashes/*
```

Because the spec includes patterns, the puller does not write `refs/main`:
downstream references must use the snapshot path
`/models/.cache/huggingface/hub/models--kindlingai--glm-5.3-exlr8-k2-k3-k4/snapshots/9e25c28a2e8808d8b2599d780521fd6af24e7558`.

## Files (this phase)

- `05-model-pull.yaml` — suspended, operator-triggered preload Job. Pull →
  verify (manifest presence, bit387 manifest parses, layer-width set spot
  check, per-file `.sha256` verification for every downloaded file) → write
  lane receipt → touch completion marker. Resumable `.part` semantics come
  from the puller.
- `kustomization.yaml` — includes only the pull Job.

## Operator runbook (one line each)

```bash
kubectl -n llm-test apply -k llm-test/conductor-workloads/workloads/glm53-exlr8-k4
kubectl -n llm-test patch job glm53-exlr8-k4-cache-pull-v1 --type=merge -p '{"spec":{"suspend":false}}'
kubectl -n llm-test logs -f job/glm53-exlr8-k4-cache-pull-v1
```

At 62.5 MB/s cap, ~357 GiB takes ~1.6 h best-case; the Job is resumable, so
interrupts cost only the in-flight file.

Re-running an already-complete pull is a cheap no-op (puller skips files
present at the expected size; verify re-hashes ~630 GiB — juicefs page cache
makes this tolerable, but don't schedule it casually).

## Deferred (next phase, NOT in this lane)

1. **Serving shape.** gr8 is shipped upstream as docker-compose-per-box
   (each box runs a container that fetches its own rank slice, peers via
   `PEERS`/`IPS`/`IPS2` or mentat, head serves :8100). The k8s shape needs a
   design pass: 4-rank Deployments (worker-first start order, per-rank
   nodeSelector) vs wrapping upstream compose; hostNetwork vs routed
   ConnectX/RoCE networking; how/whether the k8s puller's full-tree cache
   replaces gr8's per-box boot-time slice fetch (`HF_HOME` mount into the
   serving containers is the likely answer); memory-compaction sysctl on
   nodes; and a `ManagedWorkload` with `poolRef: dgx-spark` — which currently
   has `capacity.slots: 1` and 1104 Resident, so TP4 needs either pool
   capacity rethink or a second pool.
2. **TP4 capacity.** 4 Sparks of the 4-node pool fully consumed by one
   workload; 1104 (TP2) and any cygnet workloads must be relocated or the
   experiment must be scheduled around them.
3. **DFlash2 drafter.** gr8's speculative drafting uses
   `incoai/GLM-5.3-Flash-DFlash2` — CC BY-NC-ND 4.0, non-commercial. Not
   needed for basic TP4 eval; decide before adding.
4. **Model download on the serving side.** gr8 fetches from HF at first boot
   by default; we want the serving containers to read the preloaded cache.
