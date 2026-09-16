# DSV41 cooperative-MoE candidate (built, unqualified, not deployed)

This directory is an **off-by-default candidate workflow**, not a serving profile.
The proven stock deployments in `../12-dsv41-parity.yaml` are unchanged and
remain at `replicas: 0`; they still install baked `/opt/dsv41/exl3.py`.

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
- exact build command: `bash /work/input/extension/build.sh /work/input/upstream /work/output` in the pinned serving image (the archived `extension/build.sh` has the same hash).

The local binary was built in the pinned serving image from the exact archived
ExLlama headers/source. Compiler identity and build-log SHA-256 were not captured
and remain explicit `null` provenance blockers in the lock. The candidate is
**not qualified or promotable**. It intentionally does not replace the
unavailable upstream artifact pin.

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
again and run the 54-case gate independently. Applying the manifest would not run
a Job, but this repository update does not apply it.

The vendored `test_build.py` deliberately remains checksum-identical upstream and
assumes Bash exists under `/usr/bin:/bin`, which is false on this Nix host. The
local `test_vendored_build_script_on_nix_with_resolved_bash` compatibility test
resolves Bash explicitly and supplies an `NVCC` stub with that absolute shebang;
it executes the unmodified vendored `build.sh`.

## Remaining gate and promotion sequence

1. Independent review of the vendored extension, candidate provenance, manifest,
   and hashes.
2. Capture the compiler identity and SHA-256 of the original build log, bind them
   to this exact binary in the lock, and review them. If they cannot be recovered,
   the candidate remains blocked (a rebuild is a new candidate requiring all gates).
3. During an approved maintenance window with all GPU workloads stopped, stage
   the exact bundle on **chronometer** and **sextant**.
4. Unsuspend only the chronometer gate; require zero exit and final JSON
   `{"stage":"complete","checks":54,"status":"pass",...}`. Preserve logs.
5. Repeat independently on sextant and preserve its logs. A pass is
   peak-normalized numerical screening, not bitwise equality.
6. Create a separate reviewed serving candidate profile using the published
   reproduction settings (`MAX_NUM_SEQS=2`, `EXL3_TEMP_ROWS_FUSED=8`,
   `MAX_NUM_BATCHED_TOKENS=3072`, `LONG_PREFILL_TOKEN_THRESHOLD=2816`) while
   preserving 600k context, packed Engram, port 8000, worker-first ordering, and
   zero replicas in Git. Both ranks must select the same verified overlay path.
7. In a maintenance window, run worker then head; require both activation logs,
   installed-overlay hashes, health, `323` smoke, and zero restarts.
8. Run repeated matched stock/cooperative C1 and C2 A/B, then local 4/8-client,
   packed-Engram, 32K and near-600K prefill, memory-floor, sustained burn-in, and
   response-quality/regression checks.
9. Record both 54-case passes and serving A/B as `pass` in the lane lock, obtain
   explicit review approval, and only then make a **separate** manifest/profile
   promotion change. Do not reinterpret build success as qualification.

The evidence locked in the vendored report is the paired reference pass: C1
**+27.9%** and C2 aggregate **+33.1%**. The previously cited +25.3%/+35.2%
post-merge figures are not present in the locked benchmark evidence and are not
claimed here. The locked test used bounded samples; arithmetic is not bit-exact,
all nine sampled response hashes changed, near-600K and sustained production
were not repeated, and the local 8-sequence profile is unqualified.

## Rollback

Promotion must remain a profile-only choice. Drain requests, scale head down then
worker, remove the candidate overlay selection, restore the stock 8/2048 profile,
and restart worker then head. The immutable stock image/model pins and baked
`/opt/dsv41/exl3.py` remain the rollback baseline. Staged cache files are inert
when the stock overlay is selected and may remain for audit.
