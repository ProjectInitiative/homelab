#!/usr/bin/env bash
# Manual GLM 1104 cutover for the break-glass window where Conductor is NOT
# managing the dgx-spark pool (managementMode: Observe / Conductor off).
#
# Unlike cutover.sh, this script does NOT read or patch ManagedWorkloads and
# does NOT require the pool to be in Manage mode. It only scales the two lane
# Deployments, watches pods/endpoints, and runs the API smoke.
#
# Usage (run each as one command line, then paste the reported follow-ups):
#   ./manual-smoke.sh preflight   # fail-closed checks before any scaling
#   ./manual-smoke.sh up          # worker first, then head, then API smoke
#   ./manual-smoke.sh status      # current image/pods/endpoints/state
#   ./manual-smoke.sh logs        # tail both rank pod logs in the current pods
#   ./manual-smoke.sh down        # head to 0, then worker to 0 (teardown only)
#
# Prereqs: kubectl context with llm-test Deployment create/list/watch rights.
# This script never touches v14, Conductor resources, the CSI/CSI config, the
# JuiceFS cache ring, or /lane-state. Rollback is manual teardown (down) plus a
# separately reviewed v14 recovery (revert.sh needs Conductor access again).
set -euo pipefail

NS=llm-test
WORKER=glm53-flash-1104-worker
HEAD=glm53-flash-1104-head
API_SVC=glm53-flash-1104-api
STABLE_SVC=dgx-spark-backend
RENDER_SVC=glm53-flash-1104-worker-rendezvous # sanity: rendezvous svcs exist
EXPECT_IMAGE='local-registry.registry.svc.cluster.local:5000/homelab/tensorfold-glm53-flash-1104:ef2e6847aa4a-py3-v1@sha256:cc2af44e04d6a2c73a710f14df9ed58a15a4fe7d67ecbdd575f1018e98ddd04e'
WORKER_UP_TIMEOUT=${WORKER_UP_TIMEOUT:-1200}
HEAD_UP_TIMEOUT=${HEAD_UP_TIMEOUT:-2400}
WAIT_INTENT_TIMEOUT=${WAIT_INTENT_TIMEOUT:-2400}
ENDPOINT_TIMEOUT=${ENDPOINT_TIMEOUT:-600}
POLL=${POLL:-10}
SMOKE_PORT=8000
SMOKE_TIMEOUT=${SMOKE_TIMEOUT:-180}

log() { echo "$(date -u +%FT%TZ) $*" >&2; }
die() {
  log "FAIL: $*"
  log "No automatic rollback was performed. For rank diagnostics: ./manual-smoke.sh logs; node-local rank logs are /var/lib/llm-test/glm53-flash-1104-state/logs/rank{0,1}.log. Teardown is: ./manual-smoke.sh down"
  exit 1
}

need_kubectl() { command -v kubectl >/dev/null 2>&1 || die "kubectl not found on PATH"; }

deploy_image() { kubectl get deployment "$1" -n "$NS" -o 'jsonpath={.spec.template.spec.containers[0].image}'; }

image_ready() {
  local im
  im=$(deploy_image "$1") || die "cannot read $1 image"
  [ "$im" = "$EXPECT_IMAGE" ]
}

pod_ip_running() { # NAME -> pod ip if any pod is Running
  kubectl get pods -n "$NS" -l "app=$1" \
    -o 'jsonpath={range .items[*]}{.status.phase}{"|"}{.status.podIP}{"\n"}{end}' 2>/dev/null \
    | awk -F'|' '$1=="Running" && $2!="" {print $2; exit}'
}

pod_count_any() { # NAME -> non-terminating-ish pod count
  kubectl get pods -n "$NS" -l "app=$1" -o 'jsonpath={.items[*].metadata.name}' | wc -w
}

wait_pod_running() { # NAME TIMEOUT_S
  local name="$1" deadline=$(( $(date +%s) + $2 )) ip
  while :; do
    ip=$(pod_ip_running "$name") && [ -n "$ip" ] && { log "$1 has a Running pod at $ip"; return 0; }
    if [ "$(pod_count_any "$1")" = "0" ]; then
      kubectl get events -n "$NS" --sort-by=.lastTimestamp -o custom-columns=LAST:.lastTimestamp,MSG:.message 2>/dev/null | tail -4 >&2 || true
      log "TIMEOUT: $1 has no pods at all (check scheduling/events)"
      return 1
    fi
    if [ "$(date +%s)" -ge "$deadline" ]; then
      log "TIMEOUT waiting for $1 to reach Running at $ip"
      kubectl get pods -n "$NS" -l "app=$1" -o wide >&2
      return 1
    fi
    sleep "$POLL"
  done
}

wait_pod_ready() { # NAME TIMEOUT_S
  local name="$1" deadline=$(( $(date +%s) + $2 )) ok
  while :; do
    ok=$(kubectl get pods -n "$NS" -l "app=$name" -o 'jsonpath={.items[*].status.containerStatuses[0].ready}' 2>/dev/null | grep -c true || true)
    if [ "${ok:-0}" -ge 1 ]; then log "$1 has a Ready pod"; return 0; fi
    if [ "$(date +%s)" -ge "$deadline" ]; then
      log "TIMEOUT waiting for $1 Ready"
      kubectl get pods -n "$NS" -l "app=$1" -o wide >&2
      return 1
    fi
    sleep "$POLL"
  done
}

wait_scale_zero() { # NAME TIMEOUT_S
  local name="$1" deadline=$(( $(date +%s) + $2 ))
  while :; do
    if [ "$(pod_count_any "$name")" = "0" ]; then log "$name fully down"; return 0; fi
    if [ "$(date +%s)" -ge "$deadline" ]; then
      log "TIMEOUT waiting for $name pods to terminate"
      kubectl get pods -n "$NS" -l "app=$name" -o wide >&2
      return 1
    fi
    sleep "$POLL"
  done
}

endpoint_ip() { kubectl get endpoints "$1" -n "$NS" -o 'jsonpath={.subsets[*].addresses[*].ip}' 2>/dev/null | tr -s ' ' '\n' | grep -v '^$' | sort -u; }

wait_sole_endpoint_matches() { # SVC PODIP TIMEOUT_S
  local svc="$1" ip="$2" deadline=$(( $(date +%s) + $3 )) cur
  while :; do
    cur=$(endpoint_ip "$svc")
    log "$svc endpoints: ${cur:-none}"
    if [ "$cur" = "$ip" ]; then log "$svc sole endpoint matches $1 head pod ip $ip"; return 0; fi
    [ -z "$cur" ] || log "$svc endpoint set ($cur) does not match head pod $ip yet"
    if [ "$(date +%s)" -ge "$deadline" ]; then
      log "TIMEOUT waiting for $svc == $ip"
      return 1
    fi
    sleep "$POLL"
  done
}

http_ok() { curl -fsS --max-time 10 "http://$1:$SMOKE_PORT$2" 2>&1; }

cmd_preflight() {
  need_kubectl
  ctx=$(kubectl config current-context 2>&1) || ctx="(no context set)"
  log "kubectl context: $ctx"
  ns_out=$(kubectl get deployment "$WORKER" -n "$NS" -o name 2>&1) || die "cannot read namespace $NS with kubectl context '$ctx': ${ns_out}. Point kubectl at the mc/capstan cluster (server https://172.16.1.50:6443), e.g. export KUBECONFIG=<mc kubeconfig> or kubectl config use-context <mc-context>, then rerun."
  log "== preflight ($(kubectl config current-context 2>/dev/null || echo unknown)) =="
  for d in "$WORKER" "$HEAD"; do
    count=$(kubectl get deployment "$d" -n "$NS" -o 'jsonpath={.spec.replicas}')
    [ "$count" = "0" ] || die "$d spec.replicas=$count (want 0) before staging"
    image_ready "$d" || die "$d is NOT on the verified image ($EXPECT_IMAGE); wait for the Argo sync to the merged revision before scaling."
  done
  ep=$(endpoint_ip "$STABLE_SVC")
  [ -z "$ep" ] || die "stable $STABLE_SVC still has endpoints: $ep"
  kubectl get svc "$API_SVC" "$RENDER_SVC" "$STABLE_SVC" -n "$NS" >/dev/null || die "required Services missing"
  log "preflight OK: both Deployments at 0 on $EXPECT_IMAGE; $STABLE_SVC has no endpoints"
}

cmd_up() {
  need_kubectl
  cmd_preflight
  log "== stage 1/5 worker rank -> 1 =="
  kubectl scale deployment "$WORKER" -n "$NS" --replicas=1 >/dev/null || die "scaled worker failed"
  wait_pod_running "$WORKER" "$WORKER_UP_TIMEOUT" || die "worker never reached Running"
  wait_pod_ready "$WORKER" "$WAIT_INTENT_TIMEOUT" || { log "worker not ready yet (block on head rendezvous is normal; check ./manual-smoke.sh logs)"; }
  log "== stage 2/5 head rank -> 1 =="
  kubectl scale deployment "$HEAD" -n "$NS" --replicas=1 >/dev/null || die "scale head failed"
  wait_pod_running "$HEAD" "$WORKER_UP_TIMEOUT" || die "head never reached Running"
  wait_pod_ready "$HEAD" "$HEAD_UP_TIMEOUT" || die "head never became Ready (cold load ~600s; rank logs may say more)"
  hip=$(pod_ip_running "$HEAD"); [ -n "$hip" ] || die "lost head ip after Ready"
  log "== stage 3/5 stable endpoint identity =="
  wait_sole_endpoint_matches "$STABLE_SVC" "$hip" "$ENDPOINT_TIMEOUT" || die "$STABLE_SVC never matched the head"
  log "== stage 4/5 API checks at $hip:$SMOKE_PORT =="
  out=$(http_ok "$hip" /health) || die "/health failed: ${out:-no output} at $hip"
  log "health OK"
  models=$(http_ok "$hip" /v1/models) || die "/v1/models failed at $hip"
  echo "$models" | grep -q 'GLM-5.3-Flash-EXL3' || die "model not in /v1/models: $models"
  log "models OK"
  log "== stage 5/5 completion smoke (max 180s timeout each, 3 tries) =="
  ok=0
  for i in 1 2 3; do
    body=$(curl -fsS --max-time "$SMOKE_TIMEOUT" "http://$hip:$SMOKE_PORT/v1/chat/completions" \
      -H 'Content-Type: application/json' \
      -d '{"model":"GLM-5.3-Flash-EXL3","messages":[{"role":"user","content":"Reply with the single word: ready"}],"max_tokens":16}' 2>&1) && \
      echo "$body" | grep -q '"content"' && { ok=1; break; } || log "completion attempt $i failed: ${body:-no body}; retrying"
    sleep 10
  done
  [ "$ok" = 1 ] || die "completion smoke failed at $hip"
  hip_again=$(endpoint_ip "$STABLE_SVC")
  [ "$hip_again" = "$hip" ] || die "stable endpoint changed after the smoke: $hip_again (was $hip)"
  log "CUTOVER SMOKE COMPLETE: GLM 1104 serving at http://$hip:$SMOKE_PORT ($(endpoint_ip "$API_SVC") api endpoint; $STABLE_SVC sole endpoint matches)"
  log "Next: verify LiteLLM/ai-proxy walk to dgx-spark-backend returns GLM; keep v14 at 0."
}

cmd_status() {
  need_kubectl
  echo "deployments:"
  kubectl get deployment "$WORKER" "$HEAD" -n "$NS" -o custom-columns=NAME:.metadata.name,REPLICAS:.spec.replicas,READY:.status.readyReplicas,IMAGE:.spec.template.spec.containers[0].image 2>/dev/null
  echo "pods:"
  kubectl get pods -n "$NS" -l "app in ($WORKER,$HEAD)" -o wide 2>/dev/null
  echo "endpoints:"
  kubectl get endpoints "$STABLE_SVC" "$API_SVC" -n "$NS" -o wide 2>/dev/null
}

cmd_logs() {
  need_kubectl
  for d in "$WORKER" "$HEAD"; do
    pod=$(kubectl get pods -n "$NS" -l "app=$d" -o 'jsonpath={.items[0].metadata.name}' 2>/dev/null)
    if [ -n "$pod" ]; then
      echo "=== $d ($pod) tail ===" >&2
      kubectl logs -n "$NS" "$pod" --all-containers --tail=40 2>&1 | tail -60 >&2
      echo "=== $d ($pod) previous crash tail (if any) ===" >&2
      kubectl logs -n "$NS" "$pod" --all-containers --previous --tail=25 2>&1 | tail -40 >&2 || true
    else
      echo "=== $d: no pods; run up or check events ===" >&2
    fi
  done
  echo "Node-local rank logs live at /var/lib/llm-test/glm53-flash-1104-state/logs/rank{0,1}.log on the rank nodes." >&2
}

cmd_down() {
  need_kubectl
  log "teardown: head to 0 first, then worker to 0 (never reverse)"
  kubectl scale deployment "$HEAD" -n "$NS" --replicas=0 >/dev/null || die "scale head to 0 failed"
  wait_scale_zero "$HEAD" 600 || die "head pods did not go away"
  kubectl scale deployment "$WORKER" -n "$NS" --replicas=0 >/dev/null || die "scale worker to 0 failed"
  wait_scale_zero "$WORKER" 600 || die "worker pods did not go away"
  ep=$(endpoint_ip "$STABLE_SVC"); [ -z "$ep" ] || log "WARN: $STABLE_SVC still reports endpoints after teardown"
  log "TEARDOWN COMPLETE: both lanes at 0; stable endpoint empty"
}

case "${1:-}" in
  preflight) cmd_preflight ;;
  up) cmd_up ;;
  status) cmd_status ;;
  logs) cmd_logs ;;
  down) cmd_down ;;
  *) die "usage: $0 {preflight|up|status|logs|down}" ;;
esac
