#!/usr/bin/env bash
set +e
OUT="${1:-/tmp/mcp-vip-config-$(date +%Y%m%d-%H%M%S).txt}"
exec > >(tee "$OUT") 2>&1
section() { printf '\n===== %s =====\n' "$1"; }
section 'proxy pod images and readiness'
kubectl --context mc -n tailscale get pods -l app.kubernetes.io/name=mc-ingress-proxy -o wide
for pod in $(kubectl --context mc -n tailscale get pods -o name | grep 'mc-ingress-proxy'); do
  section "$pod ingress config"
  kubectl --context mc -n tailscale exec "$pod" -- sh -c 'cat /etc/proxies/ingress-config.json' 2>&1
  section "$pod tailscale serve status"
  kubectl --context mc -n tailscale exec "$pod" -- sh -c 'tailscale serve status --json || tailscale serve status' 2>&1
  section "$pod recent service errors"
  kubectl --context mc -n tailscale logs "$pod" --all-containers --since=10m 2>&1 | grep -Ei 'mcp|tcp handler|DNAT|handler|error|fail|warn' | tail -100
 done
section 'operator service state'
kubectl --context mc -n mcp-system get svc mcp-lb-mc -o jsonpath='{.status}{"\n"}'
kubectl --context mc get proxygroup mc-ingress-proxy -o yaml 2>&1 | grep -Ei -C 3 'condition|ready|available|error|message'
section 'finished'
printf 'Saved to %s\n' "$OUT"
