# gatepipe — layered content gate

A small, dependency-light pipeline for gating text (LLM prompts, emails,
documents) before it leaves an estate or reaches a model. Built on two
observations from our System One work:

1. **Deterministic regex is nearly free and extremely precise** for
   *structurally formatted* credentials (AWS/GitHub/OpenAI keys, PEMs,
   JWTs, credentialed URLs) — microseconds per prompt, zero model cost.
2. **One-token decision models (System One / Cygnet / Von / decider) are
   semantically broad and fast when warm** (~120–250 ms) — they catch the
   things regex cannot: prose-wrapped secrets, novel formats, injection
   attempts, PII in narrative, topic mentions.

So: regex for the structural, System One for the semantic, both declared
as config, all model questions fanned out **concurrently** (vLLM batches
them server-side; measured dual-question wall time ≈ single-question).

```
text ──► layer 0: regex scan ──── hard hit ──► BLOCK (skip LLM, ~0 ms)
              │ no structural hit
              ▼
         layer 1..N: System One questions (all concurrent)
         [secrets] [injection] [pii] [project-x] ...
              │
              ▼
         combine: any | all | weighted  ──► block / allow + evidence
```

## Files

| file | role |
|---|---|
| `gatepipe.py` | pipeline: `Gate`, `RegexLayer`, `SystemOneLayer` |
| `gatepipe.yaml` | the layer declaration (this is where you add goals) |
| `sec_scan.py` | layer-0 patterns + two-tier suppression |
| `gen_corpus.py` | openssl-backed synthetic corpus generator |
| `eval_gate.py` | 4-lane eval (regex/naive/tuned/layered) with confusion matrices |

## Adding a detection goal (no code)

Add a `systemone` layer to `gatepipe.yaml`. A layer is a question preset:
`type: noul`, an `instructions` block tuned for material-vs-reference
distinctions (see the secrets preset for the pattern), and `criteria`
whose first key is the "true" option. See the commented `pii` and
`project-mentions` examples in the yaml.

## Verdict combination

- `any` — any layer trips => block. Security posture (our default).
- `all` — every System One layer must trip => block. Narrow semantics.
- `weighted` — sum `weights[layer]` of tripping layers, block at
  `threshold`. Lets you run advisory layers (injection 0.3) with a
  mandatory layer (secrets 1.0) and a score cutoff.

## Failure policy (per layer)

`on_error: closed` — if the classifier errors/timeouts, the layer flags
(fail-closed; right for secrets). `open` — errors don't block (right for
advisory layers like injection/PII). The verdict carries per-layer errors
so callers can alert on degraded posture.

## Caching

`SystemOneLayer` caches `P(true)` by `(layer_name, sha256(text))` — the
content-addressed verdict cache from DEC-0021 amendment 1, per process.
Cross-session/cross-pod caching belongs in front of the endpoint (or swap
`http_transport` for a cached client).

## Measured (132-prompt synthetic corpus, Cygnet on astrolabe)

| lane | recall | FPR |
|---|---|---|
| regex alone | 1.00 | 0.000 |
| naive System One preset | 1.00 | 0.194 |
| **tuned preset (material-vs-reference)** | **1.00** | **0.000** |
| layered (regex ∨ tuned) | 1.00 | 0.000 |

The naive→tuned delta (14 FPs → 0) is the whole argument for investing in
preset wording: an uninstructed classifier blocks `API_KEY = os.environ[...]`
and `${{ secrets.X }}` references, which makes the gate unusable for
coding assistants. Tune the preset, not the threshold.

## Honest limits

- Corpus is synthetic and co-designed with the patterns/presets — it
  measures tune-ability, not field performance. Run your own data through
  `eval_gate.py` before trusting the numbers.
- Injection lane is unvalidated (needs its own positive corpus; it fired
  only on social-engineering-flavored positives here).
- 16K-token context ceiling per chunk (DEC-0021 amendment 2 chunking is
  the client's job — split on natural boundaries, OR-aggregate).
