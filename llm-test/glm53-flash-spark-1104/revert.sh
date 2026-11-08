#!/usr/bin/env bash
# GLM 1104 revert: require 1104 fully down before bringing v14 back.
# Run only after the README preflight, as an authorized operator.
set -euo pipefail
NS=llm-test
REVERT_TIMEOUT=${REVERT_TIMEOUT:-2700}     # 45m: v14 cold load was ~600s
POLL=15
INTENT_TIMEOUT=${INTENT_TIMEOUT:-120}

log() { echo "$(date -u +%FT%TZ) $*"; }
die() { log "FAIL: $*"; exit 1; }

# A successful command with an empty/missing field is not proof of intent.
read_intent() {
  local name=$1 value desired effective
  value=$(kubectl get managedworkload "$name" -n "$NS" -o 'jsonpath={.spec.desiredState}{"|"}{.status.effectiveIntent}') ||
    die "cannot read $name desired/effective intent (check authorized Conductor RBAC)"
  [[ "$value" == *'|'* ]] || die "$name intent fields are missing or malformed: $value"
  desired=${value%%|*}; effective=${value#*|}
  [[ -n "$desired" && -n "$effective" ]] || die "$name desired/effective intent is missing; refusing to proceed"
  case "$desired:$effective" in
    Resident:Resident|Standby:Standby) ;;
    *) return 1 ;;
  esac
  printf '%s|%s' "$desired" "$effective"
}

wait_intent() {
  local name=$1 want=$2 deadline=$(( $(date +%s) + INTENT_TIMEOUT )) value desired effective
  while :; do
    value=$(kubectl get managedworkload "$name" -n "$NS" -o 'jsonpath={.spec.desiredState}{"|"}{.status.effectiveIntent}') ||
      die "cannot read $name desired/effective intent (check authorized Conductor RBAC)"
    [[ "$value" == *'|'* ]] || die "$name intent fields are missing or malformed: $value"
    desired=${value%%|*}; effective=${value#*|}
    [[ -n "$desired" && -n "$effective" ]] || die "$name desired/effective intent is missing; refusing to proceed"
    if [[ "$desired" == "$want" && "$effective" == "$want" ]]; then
      log "$name intent is $want"; return 0
    fi
    (( $(date +%s) < deadline )) || die "TIMEOUT waiting for $name intent=$want (desired=$desired effective=$effective)"
    sleep 3
  done
}

wait_1104_down() {
  local name=$1 deadline=$(( $(date +%s) + 600 )) value replicas pods
  while :; do
    value=$(kubectl get deployment "$name" -n "$NS" -o 'jsonpath={.spec.replicas}') || die "cannot read deployment $name"
    [[ "$value" =~ ^[0-9]+$ ]] || die "$name spec.replicas missing or invalid: '$value'"
    replicas=$value
    # List every matching pod: terminating pods remain in this list until gone.
    pods=$(kubectl get pods -n "$NS" -l "app=$name" -o 'jsonpath={range .items[*]}{.metadata.name}{" "}{end}') || die "cannot list pods for $name"
    if [[ "$replicas" == 0 && -z "$pods" ]]; then
      log "$name has replicas=0 and no pods remain"; return 0
    fi
    (( $(date +%s) < deadline )) || die "TIMEOUT waiting for $name down (replicas=$replicas pods=${pods:-none})"
    sleep "$POLL"
  done
}

wait_v14_ready() {
  local name=$1 deadline=$(( $(date +%s) + REVERT_TIMEOUT )) value replicas ready
  while :; do
    value=$(kubectl get deployment "$name" -n "$NS" -o 'jsonpath={.spec.replicas}{"|"}{.status.readyReplicas}') || die "cannot read deployment $name"
    [[ "$value" == *'|'* ]] || die "$name deployment replica fields are missing or malformed: $value"
    replicas=${value%%|*}; ready=${value#*|}; ready=${ready:-0}
    [[ "$replicas" =~ ^[0-9]+$ && "$ready" =~ ^[0-9]+$ ]] || die "$name deployment replica fields are invalid: '$value'"
    if [[ "$replicas" == 1 && "$ready" == 1 ]]; then log "$name is ready (1/1)"; return 0; fi
    (( $(date +%s) < deadline )) || die "TIMEOUT waiting for $name ready (replicas=$replicas ready=$ready)"
    sleep "$POLL"
  done
}

endpoint_ip() {
  kubectl get endpoints "$1" -n "$NS" -o 'jsonpath={.subsets[0].addresses[0].ip}' || die "cannot read endpoints for $1"
}

log "== preflight: verify Conductor intent access before any changes =="
read_intent glm53-flash-1104 >/dev/null || die "1104 intent is not a recognized matching Resident/Standby state"
read_intent tensorfold-v14 >/dev/null || die "v14 intent is not a recognized matching Resident/Standby state"

log "== 1/4 GLM 1104 -> Standby =="
kubectl patch managedworkload glm53-flash-1104 -n "$NS" --type=merge -p '{"spec":{"desiredState":"Standby"}}' || die "failed to request 1104 Standby"
wait_intent glm53-flash-1104 Standby
wait_1104_down glm53-flash-1104-worker
wait_1104_down glm53-flash-1104-head
wait_intent glm53-flash-1104 Standby

log "== 2/4 v14 -> Resident (1104 is confirmed Standby with both Deployments and all pods down) =="
kubectl patch managedworkload tensorfold-v14 -n "$NS" --type=merge -p '{"spec":{"desiredState":"Resident"}}' || die "failed to request v14 Resident; 1104 remains Standby"
wait_intent tensorfold-v14 Resident

log "== 3/4 waiting up to ${REVERT_TIMEOUT}s for v14 ranks (worker, then head) =="
wait_v14_ready tensorfold-v14-worker
wait_v14_ready tensorfold-v14-head

log "== 4/4 stable endpoint and health check =="
deadline=$(( $(date +%s) + 600 ))
ip=""
while (( $(date +%s) < deadline )); do
  ip=$(endpoint_ip dgx-spark-backend)
  [[ -n "$ip" ]] && break
  sleep "$POLL"
done
[[ -n "$ip" ]] || die "dgx-spark-backend has no endpoints"
sleep 3
stable_ip=$(endpoint_ip dgx-spark-backend)
[[ "$stable_ip" == "$ip" ]] || die "dgx-spark-backend endpoint changed during check ($ip -> ${stable_ip:-none})"
curl -fsS --max-time 10 "http://$ip:8000/health" >/dev/null || die "health failed at $ip:8000"
sleep 3
[[ "$(endpoint_ip dgx-spark-backend)" == "$ip" ]] || die "dgx-spark-backend endpoint changed after health check"
curl -fsS --max-time 10 "http://$ip:8000/health" >/dev/null || die "stable endpoint health recheck failed at $ip:8000"

log "REVERT COMPLETE: v14 serving at http://$ip:8000"
log "Reminder: 1104 rank logs are preserved at /var/lib/llm-test/glm53-flash-1104-state/logs/ on the rank nodes."
