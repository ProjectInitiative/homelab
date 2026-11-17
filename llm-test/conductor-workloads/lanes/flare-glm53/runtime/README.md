# Flare serving image build

Wraps the upstream `Dockerfile` at a pinned revision. The upstream image is a
minimal two-stage Rust build: the `flare` binary plus RoCE userland only — no
Python, no torch, no compilers. It serves an already-prepared package.

Build (single line):

```
bash llm-test/flare-glm53/runtime/build.sh registry.taildeab2.ts.net/homelab/flare-runtime:5f37bd1
```

- Flare source: `5f37bd14062334f7687d168d58ea00567b9aa7fe`
- Published: `registry.taildeab2.ts.net/homelab/flare-runtime:5f37bd1`
  (digest `sha256:6784b907b7a05e88514e6e02d9abd5cf0813e4a5b10420c596628c94b124cf49`)

The compiler side lives in `../preparer/`. Update the `FLARE_REV` pin and
retag when adopting a new upstream revision; digest-pin the result in serving
manifests.

CI builds the same thing to GHCR on changes to this directory:
`ghcr.io/projectinitiative/flare-runtime:5f37bd1` (`.github/workflows/build-push-flare-runtime.yaml`).
If the GHCR package is private, make it public or configure image pull secrets
on the cluster before switching serving manifests to it.
