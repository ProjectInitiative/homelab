#!/usr/bin/env bash
# GLM 1104 revert: require 1104 fully down before bringing v14 back.
# Run only after the README preflight, as an authorized operator.
set -euo pipefail
NS=llm-test
REVERT_TIMEOUT=${REVERT_TIMEOUT:-2700}     # 45m: v14 cold load was ~600s
DOWN_TIMEOUT=${DOWN_TIMEOUT:-600}
ENDPOINT_TIMEOUT=${ENDPOINT_TIMEOUT:-600}
POLL_SECONDS=${POLL_SECONDS:-15}
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
    [[ "$name" == tensorfold-v14 ]] && assert_1104_down
    value=$(kubectl get managedworkload "$name" -n "$NS" -o 'jsonpath={.spec.desiredState}{"|"}{.status.effectiveIntent}') ||
      die "cannot read $name desired/effective intent (check authorized Conductor RBAC)"
    [[ "$value" == *'|'* ]] || die "$name intent fields are missing or malformed: $value"
    desired=${value%%|*}; effective=${value#*|}
    [[ -n "$desired" && -n "$effective" ]] || die "$name desired/effective intent is missing; refusing to proceed"
    if [[ "$desired" == "$want" && "$effective" == "$want" ]]; then
      log "$name intent is $want"; return 0
    fi
    (( $(date +%s) < deadline )) || die "TIMEOUT waiting for $name intent=$want (desired=$desired effective=$effective)"
    sleep "$POLL_SECONDS"
  done
}

# These match labels in the v1.4.0 and GLM 1104 Deployment templates.
no_pods_for() {
  local name=$1 pods
  pods=$(kubectl get pods -n "$NS" -l "app=$name" -o 'jsonpath={range .items[*]}{.metadata.name}{" "}{end}') || die "cannot list pods for $name"
  [[ -z "$pods" ]] || die "$name has pod(s) remaining: $pods"
}

assert_1104_down() {
  local name replicas
  local value
  value=$(kubectl get managedworkload glm53-flash-1104 -n "$NS" -o 'jsonpath={.spec.desiredState}{"|"}{.status.effectiveIntent}') ||
    die "cannot read 1104 intent while v14 is active (authorized Conductor access required)"
  [[ "$value" == 'Standby|Standby' ]] || die "1104 intent changed during v14 recovery ($value); stopping without further patches"
  for name in glm53-flash-1104-worker glm53-flash-1104-head; do
    replicas=$(kubectl get deployment "$name" -n "$NS" -o 'jsonpath={.spec.replicas}') || die "cannot read deployment $name"
    [[ "$replicas" == 0 ]] || die "$name replicas changed during v14 recovery ($replicas); stopping without further patches"
    no_pods_for "$name"
  done
}

wait_1104_down() {
  local name=$1 deadline=$(( $(date +%s) + DOWN_TIMEOUT )) replicas
  while :; do
    replicas=$(kubectl get deployment "$name" -n "$NS" -o 'jsonpath={.spec.replicas}') || die "cannot read deployment $name"
    [[ "$replicas" =~ ^[0-9]+$ ]] || die "$name spec.replicas missing or invalid: '$replicas'"
    local pods
    pods=$(kubectl get pods -n "$NS" -l "app=$name" -o 'jsonpath={range .items[*]}{.metadata.name}{" "}{end}') || die "cannot list pods for $name"
    if [[ "$replicas" == 0 && -z "$pods" ]]; then
      log "$name has replicas=0 and no pods remain"; return 0
    fi
    (( $(date +%s) < deadline )) || die "TIMEOUT waiting for $name down (replicas=$replicas pods=${pods:-none})"
    sleep "$POLL_SECONDS"
  done
}

# Return one Deployment's one Ready pod identity (name|IP|node|phase|Ready).
rank_pod_info() {
  local name=$1 result
  result=$(kubectl get pods -n "$NS" -l "app=$name" -o 'jsonpath={range .items[*]}{.metadata.name}{"|"}{.status.podIP}{"|"}{.spec.nodeName}{"|"}{.status.phase}{"|"}{range .status.conditions[?(@.type=="Ready")]}{.status}{end}{"\n"}{end}') ||
    die "cannot read pod identity for $name"
  [[ -n "$result" && "$result" != *$'\n'* ]] || die "$name must have exactly one pod; got '${result:-none}'"
  printf '%s' "$result"
}

wait_v14_ready() {
  local name=$1 deadline=$(( $(date +%s) + REVERT_TIMEOUT )) value replicas ready info
  while :; do
    assert_1104_down
    value=$(kubectl get deployment "$name" -n "$NS" -o 'jsonpath={.spec.replicas}{"|"}{.status.readyReplicas}') || die "cannot read deployment $name"
    [[ "$value" == *'|'* ]] || die "$name deployment replica fields are missing or malformed: $value"
    replicas=${value%%|*}; ready=${value#*|}; ready=${ready:-0}
    [[ "$replicas" =~ ^[0-9]+$ && "$ready" =~ ^[0-9]+$ ]] || die "$name deployment replica fields are invalid: '$value'"
    if [[ "$replicas" == 1 && "$ready" == 1 ]]; then
      info=$(rank_pod_info "$name")
      IFS='|' read -r RANK_POD RANK_IP RANK_NODE RANK_PHASE RANK_READY <<<"$info"
      [[ -n "$RANK_POD" && -n "$RANK_IP" && -n "$RANK_NODE" && "$RANK_PHASE" == Running && "$RANK_READY" == True ]] ||
        die "$name pod is not uniquely Running/Ready with IP and node: $info"
      log "$name is ready (1/1): pod=$RANK_POD ip=$RANK_IP node=$RANK_NODE"; return 0
    fi
    (( $(date +%s) < deadline )) || die "TIMEOUT waiting for $name ready (replicas=$replicas ready=$ready)"
    sleep "$POLL_SECONDS"
  done
}

endpoint_ips() {
  kubectl get endpoints "$1" -n "$NS" -o 'jsonpath={range .subsets[*].addresses[*]}{.ip}{"\n"}{end}' || die "cannot read endpoints for $1"
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

log "== 2/4 v14 -> Resident (1104 Standby and both deployments/pod sets down) =="
kubectl patch managedworkload tensorfold-v14 -n "$NS" --type=merge -p '{"spec":{"desiredState":"Resident"}}' || die "failed to request v14 Resident; 1104 remains Standby"
# CR writes are not atomic. Detect any concurrent reactivation immediately and
# on every wait/check; never attempt an automatic corrective patch.
assert_1104_down
wait_intent tensorfold-v14 Resident
assert_1104_down

log "== 3/4 waiting up to ${REVERT_TIMEOUT}s for v14 ranks (worker, then head) =="
wait_v14_ready tensorfold-v14-worker
V14_WORKER_NODE=$RANK_NODE
wait_v14_ready tensorfold-v14-head
V14_HEAD_POD=$RANK_POD
V14_HEAD_IP=$RANK_IP
V14_HEAD_NODE=$RANK_NODE
[[ "$V14_WORKER_NODE" != "$V14_HEAD_NODE" ]] || die "v14 worker and head share node $V14_HEAD_NODE"

log "== 4/4 stable endpoint and head-identity check =="
deadline=$(( $(date +%s) + ENDPOINT_TIMEOUT ))
endpoint=""
while (( $(date +%s) < deadline )); do
  assert_1104_down
  endpoints=$(endpoint_ips dgx-spark-backend)
  if [[ -n "$endpoints" ]]; then
    [[ "$endpoints" != *$'\n'* ]] || die "dgx-spark-backend has multiple endpoint addresses: $endpoints"
    endpoint=$endpoints
    break
  fi
  sleep "$POLL_SECONDS"
done
[[ -n "$endpoint" ]] || die "dgx-spark-backend has no endpoints"
[[ "$endpoint" == "$V14_HEAD_IP" ]] || die "stable endpoint $endpoint is not Ready v14 head $V14_HEAD_POD IP $V14_HEAD_IP"
assert_1104_down
curl -fsS --max-time 10 "http://$endpoint:8000/health" >/dev/null || die "health failed at $endpoint:8000"
sleep "$POLL_SECONDS"
assert_1104_down
[[ "$(endpoint_ips dgx-spark-backend)" == "$V14_HEAD_IP" ]] || die "stable endpoint changed or no longer matches v14 head"
curl -fsS --max-time 10 "http://$endpoint:8000/health" >/dev/null || die "stable endpoint health recheck failed at $endpoint:8000"
assert_1104_down

log "PROVISIONAL: v14 head/worker and stable endpoint health verified. Cache-ring mount identity/membership and API smoke still require the separate operator checks in README."
log "Inspect the v14 nodes' fresh CSI mount pods, confirm exact image/options/group and runtime membership, then run /v1/models plus a short completion smoke."
[[ -t 0 ]] || die "non-interactive run cannot confirm cache-ring and API smoke; recovery remains PROVISIONAL"
read -r -p 'After those separate checks pass, type CONFIRM_RING_AND_API_SMOKE: ' confirmation
[[ "$confirmation" == CONFIRM_RING_AND_API_SMOKE ]] || die "operator confirmation absent; recovery remains PROVISIONAL"
log "REVERT COMPLETE: v14 serving at http://$endpoint:8000; operator confirmed cache ring and API smoke"
