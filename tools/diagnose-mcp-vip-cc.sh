#!/usr/bin/env bash
# Decisive test for the astrolabe-only MCP VIP refusal.
# Theory: a stale `mcp-lb-mc` Service exists in the CC cluster (which runs on
# astrolabe). Its proxy pods would advertise the SAME VIP name
# (svc:mcp-system-mcp-lb-mc -> 100.64.72.152), and astrolabe deterministically
# pins to the local cc-ingress-proxy pod (0ms RTT) -> DNAT to a dead/absent
# ClusterIP in cc -> instant RST. Every other device pins an MC proxy -> works.
# Run from an auth k8s session (both contexts available).
set -u
CC="${CC_CONTEXT:-cc}"

echo "=== 1. Services in cc mcp-system (looking for a stale mcp-lb-mc) ==="
kubectl --context "$CC" -n mcp-system get svc -o wide

echo
echo "=== 2. Where do cc proxy pods run? ==="
kubectl --context "$CC" -n tailscale get pods -o wide 2>/dev/null | grep -E 'NAME|ingress-proxy'

echo
echo "=== 3. DNAT rules in each cc proxy boot log (any claiming 100.64.72.152?) ==="
for pod in $(kubectl --context "$CC" -n tailscale get pods -o name 2>/dev/null | grep ingress-proxy); do
  echo "--- $pod ---"
  kubectl --context "$CC" -n tailscale logs "$pod" -c tailscale 2>/dev/null \
    | grep -iE 'adding DNAT rule|vip-services' | head -8
done

echo
echo "=== 4. Tailnet-wide: which VIP services exist and which IPs? ==="
echo "(run on astrolabe:) tailscale debug netmap 2>/dev/null | grep -o '100.64.72.152[^\"]*' | head -3"
echo "(or check the cc operator's view of VIP services via its oauth creds)"

echo
echo "=== 5. Cross-check: does cc's k3s even run on astrolabe? ==="
kubectl --context "$CC" get nodes -o wide | head -5
