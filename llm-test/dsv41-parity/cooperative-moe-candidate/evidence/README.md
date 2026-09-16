# Cooperative-MoE qualification evidence

These immutable, credential-free captures bind the local candidate binary
`16191d208101a3a04b021f8a2d0da360c5ebb710c0145b2e312052a02ce40305`, pinned
serving image, GPU gates, and bounded serving A/B results.

- `cooperative_moe-build.log`, `compiler-identity.txt`: captured build provenance.
- `gate-{chronometer,sextant}.log`: independent terminal 54-case GPU gate records.
- `benchmark.py`: repo-relative implementation of the exact streaming protocol.
- `serving-stock-matched.jsonl`: stock overlay with the candidate's exact 2/3072 reproduction profile.
- `serving-cooperative.jsonl`: cooperative overlay with that same profile.
- `serving-stock-operational.jsonl`: supplemental old stock 8/2048 operational profile; not used for matched gains.
- `serving-summary.json`: three-repetition medians and matched changes.

Every measured C1 response and both streams of every C2 request completed at the
400-token bound. Matched medians were stock 30.842845123259174 / 48.11253629584001
and cooperative 43.113290591022924 / 61.47737096150947 tokens/s (C1 / C2), gains
of +39.78376644154133% / +27.778279206671197%.

The serving observation also recorded both-rank activation and hashes,
cooperative runtime, packed Engram, readiness, zero restarts, external `/health`
and `/v1/models` HTTP 200, and the exact nonthinking 323-token smoke. It does not
establish long-context, burn-in, or response-quality qualification and does not
approve promotion.

Re-run the bounded protocol from the repository root (against an explicitly
selected reviewed endpoint/profile) with:

```bash
python3 llm-test/dsv41-parity/cooperative-moe-candidate/evidence/benchmark.py \
  --profile stock-matched --url http://reviewed-endpoint \
  --output /tmp/serving-stock-matched.jsonl
```

Verify retained evidence from this directory with `sha256sum -c SHA256SUMS`.
