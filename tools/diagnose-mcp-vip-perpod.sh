#!/usr/bin/env bash
# Decisive per-proxy test: does EACH mc-ingress-proxy pod actually serve the
# MCP VIP? Uses `tailscale nc` (built into the container, no curl needed).
# Boot logs claimed all 3 pods installed the DNAT rule; this verifies the
# live data path. Run from an auth k8s session (context "mc").
set -u
CTX="${KUBE_CONTEXT:-mc}"
NS="tailscale"
VIP="100.64.72.152"
PORT="${PORT:-80}"

for pod in mc-ingress-proxy-0 mc-ingress-proxy-1 mc-ingress-proxy-2; do
  echo "===== $pod ====="
  echo "node: $(kubectl --context "$CTX" -n "$NS" get pod "$pod" -o jsonpath='{.spec.nodeName}')"
  # tailscale nc connects via the pod's OWN tailscaled -> tests the local
  # netstack + DNAT path for the VIP exactly as an external client would hit it.
  timeout 15 kubectl --context "$CTX" -n "$NS" exec "$pod" -c tailscale -- \
    tailscale nc "$VIP" "$PORT" </dev/null 2>&1 | head -5
  echo "exit=$?"
  echo
done

echo "===== control: ClusterIP reachability from each pod ====="
for pod in mc-ingress-proxy-0 mc-ingress-proxy-1 mc-ingress-proxy-2; do
  printf '%s: ' "$pod"
  timeout 15 kubectl --context "$CTX" -n "$NS" exec "$pod" -c tailscale -- \
    tailscale nc 10.43.135.212 80 </dev/null 2>&1 | head -2
  echo "exit=$?"
done
