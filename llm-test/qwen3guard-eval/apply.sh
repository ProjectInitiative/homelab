#!/usr/bin/env bash
# Build + apply the Qwen3Guard baseline eval stack.
#   1. Deployment/Service: vLLM serving Qwen/Qwen3Guard-Gen-0.6B on sextant
#   2. ConfigMap with the eval script + cygnet-bench corpus (copied, 92K)
#   3. Eval Job
# Usage: ./apply.sh            (everything)
#        ./apply.sh eval       (re-run just the eval Job against the live service)
set -euo pipefail
cd "$(dirname "$0")"
CORPUS=../../experiments/cygnet-bench/corpus

NS=llm-test

make_code_cm() {
  kubectl create configmap qwen3guard-eval-code -n "$NS" \
    --from-file=qwen3guard_eval.py \
    --from-file=prompts.jsonl="$CORPUS/prompts.jsonl" \
    --from-file=edge_cases.jsonl="$CORPUS/edge_cases.jsonl" \
    --from-file=injection.jsonl="$CORPUS/injection.jsonl" \
    --dry-run=client -o yaml | kubectl apply -f -
}

case "${1:-all}" in
  all)
    kubectl apply -f services.yaml
    make_code_cm
    kubectl apply -f eval-job.yaml
    ;;
  eval)
    kubectl delete job qwen3guard-eval -n "$NS" --ignore-not-found
    make_code_cm
    kubectl apply -f eval-job.yaml
    ;;
  *) echo "usage: $0 [all|eval]"; exit 1 ;;
esac
