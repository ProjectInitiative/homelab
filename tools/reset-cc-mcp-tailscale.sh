#!/usr/bin/env bash
set -Eeuo pipefail

CTX="${KUBE_CONTEXT:-cc}"
SERVICE_NS="mcp-system"
SERVICE="mcp-lb-cc"
OPERATOR_NS="tailscale"
OPERATOR="operator"
HOSTNAME="mcp-system-mcp-lb-cc.taildeab2.ts.net"
TMP_DIR="$(mktemp -d /tmp/cc-mcp-reset.XXXXXX)"
trap 'rm -rf "$TMP_DIR"' EXIT

section() { printf '\n===== %s =====\n' "$1"; }
run() { printf '\n$ %s\n' "$*"; "$@"; }

printf 'CC MCP Tailscale recovery\ncontext=%s\nservice=%s/%s\nhostname=%s\n' "$CTX" "$SERVICE_NS" "$SERVICE" "$HOSTNAME"

section 'preflight'
run kubectl --context "$CTX" -n "$SERVICE_NS" get svc "$SERVICE" -o wide
run kubectl --context "$CTX" -n "$SERVICE_NS" get endpointslice -l "kubernetes.io/service-name=$SERVICE" -o wide
run kubectl --context "$CTX" -n "$SERVICE_NS" get pods -l app=mcp-kubernetes -o wide

printf '\nDelete only the stale Tailscale service in the admin console:\n  svc:mcp-system-mcp-lb-cc\n\nDo not delete the Kubernetes Service, ProxyGroup, or proxy state Secrets.\nPress Enter after the console deletion is complete, or Ctrl-C to abort.\n'
read -r

section 'restart operator and wait for reconciliation'
run kubectl --context "$CTX" -n "$OPERATOR_NS" rollout restart "deployment/$OPERATOR"
run kubectl --context "$CTX" -n "$OPERATOR_NS" rollout status "deployment/$OPERATOR" --timeout=120s
sleep 8

section 'post-reconcile Kubernetes state'
run kubectl --context "$CTX" -n "$SERVICE_NS" get svc "$SERVICE" -o wide
run kubectl --context "$CTX" -n "$SERVICE_NS" get svc "$SERVICE" -o jsonpath='hostname={.status.loadBalancer.ingress[0].hostname} ip={.status.loadBalancer.ingress[0].ip}{"\n"}'
run kubectl --context "$CTX" -n "$SERVICE_NS" get endpointslice -l "kubernetes.io/service-name=$SERVICE" -o wide
run kubectl --context "$CTX" get proxygroup cc-ingress-proxy -n "$OPERATOR_NS" -o yaml | grep -Ei -C 3 'condition|ready|error|message' || true

section 'operator MCP reconciliation logs'
kubectl --context "$CTX" -n "$OPERATOR_NS" logs "deployment/$OPERATOR" --since=3m 2>&1 | grep -Ei 'mcp-lb-cc|mcp-system|error|fail' | tail -100 || true

section 'DNS and SSE test from this workstation'
if getent hosts "$HOSTNAME"; then
  set +e
  curl -sS -N --connect-timeout 5 --max-time 8 "http://$HOSTNAME/sse" -o "$TMP_DIR/body" 2>"$TMP_DIR/curl-error"
  CURL_RC=$?
  set -e
  printf 'curl_exit=%s\n' "$CURL_RC"
  if grep -q '^event: endpoint' "$TMP_DIR/body"; then
    printf 'RESULT=PASS: MCP SSE endpoint returned\n'
    sed -n '1,4p' "$TMP_DIR/body"
  else
    printf 'RESULT=FAIL: expected SSE endpoint was not returned\n'
    cat "$TMP_DIR/curl-error"
    exit 1
  fi
else
  printf 'RESULT=FAIL: hostname does not resolve: %s\n' "$HOSTNAME"
  exit 1
fi

printf '\nRESULT=CC MCP Tailscale recovery completed successfully\n'
