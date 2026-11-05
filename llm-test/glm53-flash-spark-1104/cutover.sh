#!/usr/bin/env bash
# GLM 1104 cutover: stand v14 down, bring the 1104 pair up, verify the API.
# Run as yourself (needs ManagedWorkload patch rights). Reverts via revert.sh on
# any failure or timeout. See README.md "Activation gates / rollback".
#   ./cutover.sh
set -euo pipefail
NS=llm-test
CUTOVER_TIMEOUT=${CUTOVER_TIMEOUT:-2700}   # 45m: digest + cold load ~600s + margin
POLL=15

log() { echo "$(date -u +%FT%TZ) $*"; }
die() { log "FAIL: $*"; "${BASH_SOURCE[0]%/*}/revert.sh" || true; exit 1; }

# wait_deployment NAME EXPECTED_REPLICAS TIMEOUT_S
wait_deployment() {
  local name=$1 want=$2 deadline=$(( $(date +%s) + $3 )) cur ready
  while [ "$(date +%s)" -lt "$deadline" ]; do
    cur=$(kubectl get deployment "$name" -n "$NS" -o jsonpath='{.spec.replicas}' 2>/dev/null || echo '?')
    ready=$(kubectl get deployment "$name" -n "$NS" -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo '')
    if [ "$cur" = "$want" ] && { [ "$want" = "0" ] || [ "$ready" = "1" ]; }; then
      log "$name is $want (ready=${ready:-0})"; return 0
    fi
    sleep "$POLL"
  done
  log "TIMEOUT waiting for $name (want=$want cur=$cur ready=${ready:-0})"
  return 1
}

endpoint_ip() { kubectl get endpoints "$1" -n "$NS" -o jsonpath='{.subsets[0].addresses[0].ip}' 2>/dev/null || true; }
wait_endpoint() {
  local svc=$1 ip deadline=$(( $(date +%s) + CUTOVER_TIMEOUT ))
  while [ "$(date +%s)" -lt "$deadline" ]; do
    ip=$(endpoint_ip "$svc")
    [ -n "$ip" ] && { log "$svc endpoint: $ip"; echo "$ip"; return 0; }
    sleep "$POLL"
  done
  log "TIMEOUT waiting for $svc endpoints"; return 1
}

log "== 1/5 v14 -> Standby (Conductor recreates the pair down) =="
kubectl patch managedworkload tensorfold-v14 -n "$NS" --type=merge -p '{"spec":{"desiredState":"Standby"}}'
wait_deployment tensorfold-v14-head 0 600 || die "v14 head did not scale down"
wait_deployment tensorfold-v14-worker 0 600 || die "v14 worker did not scale down"

log "== 2/5 GLM 1104 -> Resident (launcher self-gates on MemAvailable) =="
kubectl patch managedworkload glm53-flash-1104 -n "$NS" --type=merge -p '{"spec":{"desiredState":"Resident"}}'

log "== 3/5 waiting up to ${CUTOVER_TIMEOUT}s for both 1104 ranks (check /state/logs/rank*.log on the rank nodes) =="
# The worker is the flaky one historically; surface its restarts while waiting.
( while sleep 60; do
    w=$(kubectl get deployment glm53-flash-1104-worker -n "$NS" -o jsonpath='{.spec.replicas},{.status.readyReplicas}' 2>/dev/null || echo '?')
    h=$(kubectl get deployment glm53-flash-1104-head -n "$NS" -o jsonpath='{.spec.replicas},{.status.readyReplicas}' 2>/dev/null || echo '?')
    echo "$(date -u +%T) worker(desired,ready)=$w head(desired,ready)=$h"
  done ) &
WATCH_PID=$!
trap 'kill "$WATCH_PID" 2>/dev/null || true' EXIT
wait_deployment glm53-flash-1104-worker 1 "$CUTOVER_TIMEOUT" || die "1104 worker never became ready"
wait_deployment glm53-flash-1104-head 1 "$CUTOVER_TIMEOUT" || die "1104 head never became ready"

log "== 4/5 endpoint + API checks =="
ip=$(wait_endpoint glm53-flash-1104-api) || die "no endpoint on glm53-flash-1104-api"
curl -fsS --max-time 10 "http://$ip:8000/health" >/dev/null || die "health failed at $ip:8000"
log "health OK"
models=$(curl -fsS --max-time 10 "http://$ip:8000/v1/models") || die "/v1/models failed at $ip:8000"
echo "$models" | grep -q 'GLM-5.3-Flash-EXL3' || die "model GLM-5.3-Flash-EXL3 not in /v1/models: $models"
log "models OK"

log "== 5/5 greedy completion smoke =="
ok=0
for i in 1 2 3; do
  if curl -fsS --max-time 120 "http://$ip:8000/v1/chat/completions" \
      -H 'Content-Type: application/json' \
      -d '{"model":"GLM-5.3-Flash-EXL3","messages":[{"role":"user","content":"Reply with the single word: ready"}],"max_tokens":16}' \
      | grep -q '"content"'; then ok=1; break; fi
  log "completion attempt $i failed; retrying"; sleep 20
done
[ "$ok" = 1 ] || die "completion smoke failed against $ip:8000"

log "CUTOVER COMPLETE: GLM 1104 serving at http://$ip:8000 (stable Service dgx-spark-backend follows the alias)"
log "Reminder: confirm dgx-spark-backend now points at the 1104 head and v14 stays Standby."
