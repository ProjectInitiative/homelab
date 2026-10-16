#!/usr/bin/env bash
# Apply falsification deployments + run both eval jobs.
# Usage: ./apply.sh [all|eval]
set -euo pipefail
cd "$(dirname "$0")"
CORPUS=../../experiments/cygnet-bench/corpus
NS=llm-test

make_code_cm() {
  kubectl create configmap guard-falsify-code -n "$NS" \
    --from-file=guard_eval.py \
    --from-file=prompts.jsonl="$CORPUS/prompts.jsonl" \
    --from-file=edge_cases.jsonl="$CORPUS/edge_cases.jsonl" \
    --from-file=injection.jsonl="$CORPUS/injection.jsonl" \
    --dry-run=client -o yaml | kubectl apply -f -
}

eval_job() { # name base model style out
  kubectl delete job "$1" -n "$NS" --ignore-not-found
  cat <<YAML | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: $1
  namespace: $NS
spec:
  backoffLimit: 0
  template:
    metadata: { labels: { app: $1 } }
    spec:
      restartPolicy: Never
      containers:
        - name: eval
          image: python:3.12-slim
          env:
            - { name: GUARD_BASE, value: "$2" }
            - { name: GUARD_MODEL, value: "$3" }
            - { name: GUARD_STYLE, value: "$4" }
          command: ["sh", "-c", "python3 /app/guard_eval.py --concurrency 8 --out /results-mnt/$5"]
          volumeMounts:
            - { name: app, mountPath: /app, readOnly: true }
            - { name: results, mountPath: /results-mnt }
      volumes:
        - name: app
          configMap: { name: guard-falsify-code }
        - name: results
          persistentVolumeClaim: { claimName: model-cache }
YAML
}

case "${1:-all}" in
  all)
    kubectl apply -f services.yaml
    make_code_cm
    eval_job guard-eval-8b http://qwen3guard-8b.llm-test.svc.cluster.local:80 "Qwen/Qwen3Guard-Gen-8B" qwen3guard qwen3guard-8b-eval.json
    eval_job guard-eval-granite http://granite-guardian.llm-test.svc.cluster.local:80 "ibm-granite/granite-guardian-3.1-2b" granite granite-guardian-eval.json
    ;;
  eval)
    make_code_cm
    eval_job guard-eval-8b http://qwen3guard-8b.llm-test.svc.cluster.local:80 "Qwen/Qwen3Guard-Gen-8B" qwen3guard qwen3guard-8b-eval.json
    eval_job guard-eval-granite http://granite-guardian.llm-test.svc.cluster.local:80 "ibm-granite/granite-guardian-3.1-2b" granite granite-guardian-eval.json
    ;;
  *) echo "usage: $0 [all|eval]"; exit 1 ;;
esac
