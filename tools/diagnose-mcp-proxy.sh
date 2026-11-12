#!/usr/bin/env bash
set +e

OUT="${1:-/tmp/mcp-proxy-diagnostics-$(date +%Y%m%d-%H%M%S).txt}"
CTX="mc"
exec > >(tee "$OUT") 2>&1

section() { printf '\n\n===== %s =====\n' "$1"; }
run() { printf '\n$ %s\n' "$*"; "$@"; printf 'exit=%s\n' "$?"; }

printf 'MCP proxy diagnostics\nstarted=%s\noutput=%s\n' "$(date -Is)" "$OUT"

section 'client identity and route'
run hostname
run tailscale ip -4
run tailscale status --json | python3 -c 'import json,sys; d=json.load(sys.stdin); s=d.get("Self",{}); print({k:s.get(k) for k in ("HostName","DNSName","TailscaleIPs","Tags","UserID")})'
run tailscale whois 100.64.72.152
run tailscale whois 100.83.21.3
run tailscale ping --c 3 100.64.72.152

section 'DNS and TCP/HTTP tests'
run getent ahostsv4 mcp-system-mcp-lb-mc.taildeab2.ts.net
run getent ahostsv6 mcp-system-mcp-lb-mc.taildeab2.ts.net
run nc -vz -w 5 mcp-system-mcp-lb-mc.taildeab2.ts.net 80
run curl -v --connect-timeout 5 --max-time 10 -N http://mcp-system-mcp-lb-mc.taildeab2.ts.net/sse -o /tmp/mcp-sse-diagnostic-body

section 'MCP Kubernetes Service and endpoints'
run kubectl --context "$CTX" -n mcp-system get svc mcp-lb-mc -o wide
run kubectl --context "$CTX" -n mcp-system get svc mcp-lb-mc -o yaml
run kubectl --context "$CTX" -n mcp-system get endpointslice -l kubernetes.io/service-name=mcp-lb-mc -o wide
run kubectl --context "$CTX" -n mcp-system get pods -l app=mcp-kubernetes -o wide
run kubectl --context "$CTX" -n mcp-system get events --sort-by=.lastTimestamp

section 'ProxyGroup and proxy pods'
run kubectl --context "$CTX" get proxygroup -A -o wide
run kubectl --context "$CTX" get pods -A -o wide | grep -E 'mc-ingress-proxy|tailscale.*proxy|proxy.*tailscale'
run kubectl --context "$CTX" -n tailscale get pods -o wide

for pod in $(kubectl --context "$CTX" -n tailscale get pods -o name 2>/dev/null | grep 'mc-ingress-proxy'); do
  section "logs $pod"
  kubectl --context "$CTX" -n tailscale logs "$pod" --all-containers --tail=200 2>&1 | grep -Ei 'mcp|mcp-lb|listen|serve|error|warn|fail|proxy|80|8080' | tail -120
  printf 'log-filter-exit=%s\n' "$?"
done

section 'Tailscale operator logs mentioning MCP or proxy registration'
run kubectl --context "$CTX" -n tailscale logs deploy/operator --all-containers --tail=500 2>/dev/null | grep -Ei 'mcp|mcp-lb|proxygroup|proxy group|service|error|warn|fail' | tail -200

section 'complete'
printf 'Diagnostics saved to %s\n' "$OUT"
