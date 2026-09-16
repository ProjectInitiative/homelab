# DSV41 cooperative-MoE candidate (serving-validated, promotion unapproved)

This directory contains an **off-by-default candidate workflow** and separate
zero-replica serving and matched-stock overlays. The proven stock manifest in
`../12-dsv41-parity.yaml` is byte-unchanged and remains the default adoption at
`replicas: 0`; stock still installs baked `/opt/dsv41/exl3.py`. The candidate
serving A/B passed and the candidate is currently observed live and ready, but
promotion remains explicitly unapproved. Repository manifests remain at
`replicas: 0`; this record does not apply or scale anything.

## Locked state

- reviewed upstream: `f083d7e4ccc8cc1083ef739945a3114f54a8bef5`;
- stock image: `sha256:2f0cf3adc0f989c1d446be274df864eb799630175f604c3b22b71b7205971dce`;
- stock/model/Engram pins: unchanged (see `../../lanes/dsv41/upstream.lock.json`);
- upstream native artifact: `a09a589cbdcecb5372991c7b091d732236d58bc5f5aea14ab91e38e426f08d78`, unavailable in Git and Releases;
- locally built candidate: `16191d208101a3a04b021f8a2d0da360c5ebb710c0145b2e312052a02ce40305`;
- pristine upstream `runtime.py`: `9f1d10ffc39ac4433828a000c4932a4a773b00acadd80b46c7568f494a77b2fb`;
- generated candidate `runtime.py`: `2d33c5cd57c447b4d6545abfb59356ca7ee9cefe8aa2e4fe2c2023fe09bf35de` (the single upstream binary pin is replaced with the local candidate pin);
- exact pinned ExLlama checkout: `turboderp-org/exllamav3@02aef45cd681b960a00afcd0749a4ab99e6c1bfe`;
- build-input archive `dsv41-coop-build-input.tgz`: `f0760e9cd4bd5019f87b38df6aa788123794fb541f2e58998eae52c8a0d5b32b`;
- build script `extensions/cooperative_moe/build.sh`: `0eca829cf4045ea35c2b0a7a422eeef8abdabdedc68834084aad4f64a1f4b048`;
- exact build command: `bash /work/input/extension/build.sh /work/input/upstream /work/output` in the pinned serving image (the archived `extension/build.sh` has the same hash);
- compiler identity: `nvcc: NVIDIA (R) Cuda compiler driver; Cuda compilation tools, release 13.0, V13.0.88; Build cuda_13.0.r13.0/compiler.36424714_0`;
- build log SHA-256: `c3b122a7ddaf2aa684ce9a8326e6d385bb18ca1a17e0dbb25f91ec3a6c4f2059`.

The exact bundle staged successfully on both nodes. Chronometer passed 54/54
with strict counts raw `6124458` and post-bf16 `3912212`; sextant passed 54/54
with strict counts raw `6124464` and post-bf16 `3912165`. Both used the 0.3%
reference-peak numerical screen. These are synthetic independent GPU gate
results, not distributed serving verification: `distributed_serving_verified`
is false on both nodes because those fixture gates did not themselves verify
serving. Serving A/B passed separately and promotion remains false. The complete
build log, compiler identity, and both gate logs are retained under
`evidence/` and checksum-locked by `evidence/SHA256SUMS`; the unit tests parse
those captures and compare their terminal records to `upstream.lock.json`.
The candidate intentionally does not replace the unavailable upstream artifact
pin or the current stock adoption.

## Offline bundle preparation

No native `.so` is stored in Git or a ConfigMap. On a trusted offline host,
create an **input** directory containing the local binary plus pristine vendored
runtime and tests. The generator verifies every input, requires exactly one
upstream `a09a589c…` pin in pristine `runtime.py`, and exclusively creates a
separate five-file output bundle with that pin replaced by `16191d20…`. It never
modifies the input or vendor tree, and refuses an existing output directory.

```bash
REPO=$(pwd -P)
mkdir /trusted/candidate-input
install -m 0444 /trusted/local-build/cooperative_moe.so /trusted/candidate-input/
install -m 0444 \
  "$REPO/llm-test/lanes/dsv41/vendor/extensions/cooperative_moe/runtime.py" \
  "$REPO/llm-test/lanes/dsv41/vendor/extensions/cooperative_moe/test_cuda_integration.py" \
  "$REPO/llm-test/lanes/dsv41/vendor/tests/test_exl3_overlay.py" \
  /trusted/candidate-input/
python3 "$REPO/llm-test/dsv41-parity/cooperative-moe-candidate/prepare_candidate.py" \
  --stock "$REPO/llm-test/lanes/dsv41/vendor/overlay/exl3.py" \
  --artifacts /trusted/candidate-input \
  --output-directory /trusted/candidate-bundle
(cd /trusted/candidate-bundle && sha256sum -c \
  "$REPO/llm-test/dsv41-parity/cooperative-moe-candidate/SHA256SUMS")
```

Copy the five verified files out-of-band to the existing `model-cache` PVC path
`/models/dsv41-cooperative-moe/f083d7e-local-16191d2/`. The repository provides
no downloader because there is no trusted upstream binary location. Never relax
a hash to accept a different build.

`01-stage-and-gate.yaml` contains only a ConfigMap with text scripts/checksums and
four versioned Jobs. Every Job has `spec.suspend: true`, a 30-minute active
deadline, and a three-day finished-object TTL. The two stage Jobs copy verified
bytes to each node's existing vLLM host cache; the two GPU Jobs verify the cache
again and run the 54-case gate independently. The checksum ConfigMap deliberately
uses `SHA256SUMS: |` to retain the final newline, and the copy loop uses
`while read ... || [ -n ... ]` so a final record is never omitted even if a
producer drops that newline. Applying the manifest would not run a Job, but this
repository update does not apply it.

The vendored `test_build.py` deliberately remains checksum-identical upstream and
assumes Bash exists under `/usr/bin:/bin`, which is false on this Nix host. The
local `test_vendored_build_script_on_nix_with_resolved_bash` compatibility test
resolves Bash explicitly and supplies an `NVCC` stub with that absolute shebang;
it executes the unmodified vendored `build.sh`.

## Zero-replica serving candidate

`serving/` renders the stock parity resources with the original Deployment names,
so a reviewed apply updates the stopped lane and retains existing Service routing.
Both ranks select `dsv41-exl3-coop-candidate-profile` and execute the same
fail-closed activation wrapper. The wrapper verifies all five staged hashes,
verifies baked stock overlay `ccdc69bf…`, installs `exl3-cooperative.py`, verifies
the installed hash, echoes the activation hashes, and only then execs the existing
head or worker launch script. Both ranks use the already-staged node-local path
under `/root/.cache/vllm`. There is no fallback to stock after candidate selection.

The candidate profile preserves the pinned image/model resources, 600k context,
packed rank-local Engram PVCs, host port 8000, DSpark k=3, readiness flow, and
worker-first operation. Its reproduction settings are exactly
`MAX_NUM_SEQS=2`, `MAX_NUM_BATCHED_TOKENS=3072`, `EXL3_TEMP_ROWS_FUSED=8`,
`LONG_PREFILL_TOKEN_THRESHOLD=2816`, `GLM53_WARMUP_MAX_CONCURRENCY=2`,
`DSV41_EXL3_SERIAL_STREAMS=1`, and `VLLM_DISABLE_SHARED_EXPERTS_STREAM=1`.
Both Deployments remain `replicas: 0` after apply.

From this directory, offline render and reviewed apply are:

```bash
kubectl kustomize serving --load-restrictor=LoadRestrictionsNone > /tmp/dsv41-coop-serving.yaml
kubectl kustomize serving --load-restrictor=LoadRestrictionsNone | kubectl apply -f -
```

The upward stock resource requires `LoadRestrictionsNone`; do not use or imply
`kubectl apply -k`. Applying the render still starts nothing.

## Matched stock control and activation

`stock-control/` renders the unchanged stock base and baked
`/opt/dsv41/exl3.py`, but selects the exact same 2/3072 reproduction profile used
by the candidate. Its distinct ConfigMap is
`dsv41-exl3-stock-matched-profile`; both original Deployment names and zero
replicas are preserved. Render and reviewed apply from this directory:

```bash
kubectl kustomize stock-control --load-restrictor=LoadRestrictionsNone > /tmp/dsv41-stock-matched.yaml
kubectl kustomize stock-control --load-restrictor=LoadRestrictionsNone | kubectl apply -f -
```

Applying either overlay starts nothing. In an approved maintenance window,
activate the selected overlay explicitly in worker-first order:

```bash
kubectl -n llm-test scale deployment/dsv41-exl3-worker --replicas=1
kubectl -n llm-test rollout status deployment/dsv41-exl3-worker
kubectl -n llm-test scale deployment/dsv41-exl3-head --replicas=1
kubectl -n llm-test rollout status deployment/dsv41-exl3-head
```

## Recorded serving result

The checksum-locked `evidence/` records three repetitions each of exact bounded
streaming C1/C2. Matched stock medians are 30.842845123259174 / 48.11253629584001
and cooperative medians are 43.113290591022924 / 61.47737096150947 tokens/s,
for +39.78376644154133% / +27.778279206671197% C1/C2. Every measured request
completed the 400-token bound. The old stock 8/2048 medians
33.57196678872021 / 46.14851124739707 are supplemental, not the matched control.

The live observation captured both rank activations, activation hashes,
cooperative runtime, packed Engram, readiness, zero restarts, external `/health`
and `/v1/models` HTTP 200, and exact nonthinking 323-token smoke. See
`evidence/README.md`, `serving-summary.json`, and the repo-relative
`evidence/benchmark.py` for the exact protocol and reproduction command.

## Remaining gate and promotion sequence

1. Independently review the extension, build/GPU evidence, serving overlays,
   checksum-locked A/B captures, and this state transition.
2. Complete local 4/8-client, packed-Engram, 32K and near-600K prefill,
   memory-floor, sustained burn-in, and response-quality/regression checks.
3. Obtain explicit promotion approval. Only then mark the candidate `qualified`
   or make a separate feature/profile promotion change. Serving A/B pass is not
   approval and does not change the current stock adoption.

The evidence locked in the vendored report is the paired reference pass: C1
**+27.9%** and C2 aggregate **+33.1%**. The previously cited +25.3%/+35.2%
post-merge figures are not present in the locked benchmark evidence and are not
claimed here. The locked test used bounded samples; arithmetic is not bit-exact,
all nine sampled response hashes changed, near-600K and sustained production
were not repeated, and the local 8-sequence profile is unqualified.

## Rollback

Promotion must remain a profile-only choice. Drain requests, scale head down then
worker, run `kubectl apply -f ../12-dsv41-parity.yaml` from this directory to
restore the stock 8/2048 profile at replicas zero, and restart worker then head
only after approval. For a matched-control rollback, apply `stock-control/` with
the same reviewed render pipeline; it also remains replicas zero until explicitly
scaled worker then head. The immutable stock image/model pins and baked
`/opt/dsv41/exl3.py` remain the rollback baseline. Staged cache files are inert
when stock is selected and may remain for audit.
