# guard-falsify — is the 2.6% a domain gap or a capability wall?

Two probe models on sextant (shared GPU, no device-plugin request — see
qwen3guard-eval/services.yaml for the pattern):

- **qwen3guard-8b** (port 8892→svc `qwen3guard-8b`): same Qwen3Guard
  protocol at 13× size. **Result: strict recall 0.026 / FPR 0.000 —
  identical to the 0.6B.** The taxonomy gap is definitional; scaling the
  generic guard does nothing. Capability wall ruled out.
- **granite-guardian-3.1-2b** (port 8893→svc `granite-guardian`): "bring
  your own risk" definitions via `chat_template_kwargs.guardian_config`.
  Two lanes per prompt (default harm + umbrella leak/injection definition).
  **Result: recall 0.947 / FPR 0.795** — catches 108/114 threats with a
  custom definition but flags 79.5% of benign traffic (placeholders,
  fixtures, redacted values). Right instincts, no discrimination —
  inference-time risk definitions alone don't calibrate.

Latency: 8B p50 901ms; granite 2B p50 302ms — both fine for batch lanes.

## Conclusion

Fine-tuning is the path, and the gap is the data. See
`../rk3588-classifier-data/` for the training-data plan and SFT job.

## Usage

```sh
cd ~/development/homelab/llm-test/guard-falsify && ./apply.sh        # deploy + eval
cd ~/development/homelab/llm-test/guard-falsify && ./apply.sh eval   # re-run evals
kubectl -n llm-test logs -f job/guard-eval-8b
```

Results: model-cache PVC `qwen3guard-8b-eval.json` / `granite-guardian-eval.json`.

## Files

- `services.yaml` — both deployments + services (vLLM v0.30.0, sextant-pinned)
- `guard_eval.py` — generic eval (GUARD_STYLE=qwen3guard|granite|finetuned;
  waits for engine health itself), same corpus ConfigMap pattern
- `apply.sh` — all|eval
