#!/usr/bin/env bash
# Build + apply the cygnet-classifier production stack.
# The ConfigMap is built from real files (no fragile YAML embedding):
#   cygnet_shim.py   — System One shim (one-token letter readout over vLLM)
#   questions.yaml   — question presets (email triage, secrets, PII)
# Usage: ./apply.sh   (idempotent; restarts the Deployment only if the CM changed)
set -euo pipefail
cd "$(dirname "$0")"

NS=llm-test
CM_NAME=cygnet-prod-config

kubectl create configmap "$CM_NAME" -n "$NS" \
  --from-file=cygnet_shim.py \
  --from-file=questions.yaml \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl apply -f k8s-production.yaml

# If the CM content changed, bounce the pod so it picks up the new files.
if ! kubectl get deployment cygnet-classifier -n "$NS" \
     -o jsonpath='{.spec.template.metadata.annotations.config-hash}' 2>/dev/null \
   | grep -q "$(kubectl get configmap "$CM_NAME" -n "$NS" -o jsonpath='{.metadata.resourceVersion}')"; then
  echo "config changed -> restarting deployment"
  kubectl set env deployment/cygnet-classifier -n "$NS" \
    CONFIG_HASH="$(kubectl get configmap "$CM_NAME" -n "$NS" -o jsonpath='{.metadata.resourceVersion}')"
fi

kubectl get pods -n "$NS" -l app=cygnet-classifier
