#!/usr/bin/env bash
# GLM 1104 revert: stand 1104 down, bring v14 back, verify the stable endpoint.
# Run as yourself. Idempotent; safe to run repeatedly.
#   ./revert.sh
set -euo pipefail
NS=llm-test
REVERT_TIMEOUT=${REVERT_TIMEOUT:-2700}     # 45m: v14 cold load was ~600s
POLL=15

log() { echo "$(date -u +%FT%TZ) $*"; }
die() { log "FAIL: $*"; exit 1; }

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

log "== 1/4 GLM 1104 -> Standby =="
kubectl patch managedworkload glm53-flash-1104 -n "$NS" --type=merge -p '{"spec":{"desiredState":"Standby"}}' || log "patch failed (already Standby?)"
wait_deployment glm53-flash-1104-worker 0 600 || log "WARN: 1104 worker still up; continuing"
wait_deployment glm53-flash-1104-head 0 600 || log "WARN: 1104 head still up; continuing"

log "== 2/4 v14 -> Resident =="
kubectl patch managedworkload tensorfold-v14 -n "$NS" --type=merge -p '{"spec":{"desiredState":"Resident"}}'

log "== 3/4 waiting up to ${REVERT_TIMEOUT}s for v14 ranks (cold load was ~600s) =="
wait_deployment tensorfold-v14-worker 1 "$REVERT_TIMEOUT" || die "v14 worker never became ready"
wait_deployment tensorfold-v14-head 1 "$REVERT_TIMEOUT" || die "v14 head never became ready"

log "== 4/4 stable endpoint check =="
deadline=$(( $(date +%s) + 600 ))
ip=""
while [ "$(date +%s)" -lt "$deadline" ]; do
  ip=$(endpoint_ip dgx-spark-backend)
  [ -n "$ip" ] && break
  sleep "$POLL"
done
[ -n "$ip" ] || die "dgx-spark-backend has no endpoints"
curl -fsS --max-time 10 "http://$ip:8000/health" >/dev/null || die "health failed at $ip:8000"

log "REVERT COMPLETE: v14 serving at http://$ip:8000"
log "Reminder: 1104 rank logs are preserved at /var/lib/llm-test/glm53-flash-1104-state/logs/ on the rank nodes."
