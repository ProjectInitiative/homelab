#!/usr/bin/env bash
# Check whether every mc-ingress-proxy pod actually serves the MCP VIP.
# Decisive test: astrolabe TCP-RSTs on 100.64.72.152:80 while ping/other
# VIPs work -> suspect one or more proxies lack the DNAT rule.
# Run from an auth k8s session (context "mc").
set -u
CTX="${KUBE_CONTEXT:-mc}"
NS="tailscale"
VIP="100.64.72.152"

for pod in mc-ingress-proxy-0 mc-ingress-proxy-1 mc-ingress-proxy-2; do
  echo "===== $pod ====="

  echo "--- boot log: DNAT rules added ---"
  kubectl --context "$CTX" -n "$NS" logs "$pod" -c tailscale 2>/dev/null \
    | grep 'adding DNAT rule' | tail -8

  echo "--- live nft ruleset: MCP VIP ---"
  kubectl --context "$CTX" -n "$NS" exec "$pod" -c tailscale -- \
    nft list ruleset 2>/dev/null | grep -c "$VIP" || echo "0 (VIP NOT in ruleset)"

  echo "--- live nft ruleset: all VIP DNAT targets ---"
  kubectl --context "$CTX" -n "$NS" exec "$pod" -c tailscale -- \
    nft list ruleset 2>/dev/null | grep -E 'dnat|100\.64\.|100\.7[12]\.|100\.9[0]\.' | head -10

  echo "--- ingress-config mounted in pod ---"
  kubectl --context "$CTX" -n "$NS" exec "$pod" -c tailscale -- \
    cat /etc/proxies/ingress-config 2>/dev/null | head -3

  echo
done

echo "===== proxy pod ages (were all recreated post-operator-upgrade?) ====="
kubectl --context "$CTX" -n "$NS" get pods -l app.kubernetes.io/name=mc-ingress-proxy -o wide 2>/dev/null \
  || kubectl --context "$CTX" -n "$NS" get pods -o wide | grep mc-ingress-proxy
