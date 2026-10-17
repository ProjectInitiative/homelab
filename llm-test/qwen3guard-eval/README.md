# qwen3guard-eval — RK3588 guard baseline (step 1 of rk3588-security-classifier)

Unmodified **Qwen/Qwen3Guard-Gen-0.6B** served by vLLM on **sextant** (the DGX
Spark without tensorfold), evaluated against the **cygnet-bench security corpus**
(231 prompts: main/edge/injection) to establish the fine-tuning headroom.

Why this model first: 0.6B guard with three-tier safety + PII/Jailbreak
categories, 1.19M-prompt training corpus, and Qwen3-0.6B is RKLLM-benchmarked
on RK3588 (33 tok/s, TTFT 199ms @128 ctx, ~0.8 GiB w8a8) — the closest
ready-made proxy for the edge target.

GPU sharing: cygnet-classifier-nv already runs on sextant at
`--gpu-memory-utilization 0.26`; this lane takes 0.10 (~12GiB of the GB10's
128GiB unified). Weights live in the shared model-cache PVC HF cache
(`HF_HOME=/models/.cache/huggingface`), downloaded on first boot.

## Usage

```sh
cd ~/development/homelab/llm-test/qwen3guard-eval && ./apply.sh
```

Then watch:

```sh
kubectl -n llm-test logs -f deploy/qwen3guard
```

Re-run just the eval (new corpus or script tweaks, no vLLM reboot):

```sh
cd ~/development/homelab/llm-test/qwen3guard-eval && ./apply.sh eval && kubectl -n llm-test logs -f job/qwen3guard-eval
```

Results land on the model-cache PVC at
`qwen3guard-eval/guard-eval.json` (same RWX volume cygnet uses), plus a
console summary: strict (Unsafe only) and loose (Unsafe+Controversial)
confusion matrices, a p_unsafe threshold sweep (logprobs on the verdict
token), per-corpus + per-category breakdown, guard-emitted policy categories,
and latency p50/p95.

## Files

- `services.yaml` — Deployment (vLLM v0.30.0, runtimeClassName nvidia,
  sextant-pinned, TRITON_LIBCUDA_PATH symlink dance per cygnet) + Service
- `eval-job.yaml` — eval Job (python:3.12-slim), ConfigMap built by apply.sh
- `qwen3guard_eval.py` — the eval script
- `apply.sh` — ConfigMap build + apply (all|eval)

## Read-out

The decision this feeds: does the generic 0.6B guard clear the cygnet bar
(secrets recall 1.00 / FPR 0.00, injection recall 1.00 / FPR 0.00)? Almost
certainly not — the point is to *measure the gap* per category, since that
gap is exactly the fine-tuning target (DEC-0037 tier policy: the RK3588 model
must earn independent deployment on FN/FP/p95 before replacing escalation to
GLM-5.3/cygnet).

Known fit risks for the read-out: Qwen3Guard has no native
"secrets/credentials" category (closest is PII — account passwords), and its
policy categories were not tuned for homelab/agent-traffic shape; the
category breakdown is the signal for the training-data plan in
keel projects/rk3588-security-classifier.md.
