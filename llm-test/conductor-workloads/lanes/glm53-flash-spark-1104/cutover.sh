#!/usr/bin/env bash
# GLM 1104 cutover: stand v14 down, bring the 1104 pair up, verify the API.
# Run as yourself (needs ManagedWorkload patch rights). This script never rolls
# back automatically; on failure, stop/inspect 1104 and run revert.sh explicitly
# after an authorized operator confirms the rollback state.
#   ./cutover.sh
set -euo pipefail
NS=llm-test
CUTOVER_TIMEOUT=${CUTOVER_TIMEOUT:-2700}   # 45m: digest + cold load ~600s + margin
DOWN_TIMEOUT=${DOWN_TIMEOUT:-600}
ENDPOINT_TIMEOUT=${ENDPOINT_TIMEOUT:-600}
INTENT_TIMEOUT=${INTENT_TIMEOUT:-120}
POLL=${POLL:-15}
WATCH_INTERVAL=${WATCH_INTERVAL:-60}

# Keep command substitutions machine-readable: endpoint/IP helpers print only
# their value to stdout, while all operator-facing diagnostics go to stderr.
log() { echo "$(date -u +%FT%TZ) $*" >&2; }
die() {
  log "FAIL: $*"
  log "No automatic rollback was performed. Do not scale or touch Deployments; inspect intents and run revert.sh only after an authorized operator confirms rollback."
  exit 1
}

read_pool_mode() {
  local mode
  mode=$(kubectl get resourcepool dgx-spark -n "$NS" -o 'jsonpath={.spec.managementMode}') || return 1
  [[ -n "$mode" ]] || return 1
  printf '%s' "$mode"
}

# Return desired|effective, refusing successful kubectl calls with missing data.
read_intent() {
  local name=$1 value desired effective
  value=$(kubectl get managedworkload "$name" -n "$NS" -o 'jsonpath={.spec.desiredState}{"|"}{.status.effectiveIntent}') || return 1
  [[ "$value" == *'|'* ]] || return 1
  desired=${value%%|*}; effective=${value#*|}
  [[ -n "$desired" && -n "$effective" ]] || return 1
  case "$desired:$effective" in
    Resident:Resident|Standby:Standby|Resident:Standby|Standby:Resident)
      printf '%s' "$value"; return 0 ;;
    *) return 1 ;;
  esac
}

wait_intent() {
  local name=$1 want=$2 deadline=$(( $(date +%s) + INTENT_TIMEOUT )) value
  while :; do
    value=$(read_intent "$name") || die "cannot read a complete $name intent while waiting; refusing further changes"
    if [[ "$value" == "$want|$want" ]]; then
      log "$name intent is $want"; return 0
    fi
    if (( $(date +%s) >= deadline )); then
      log "TIMEOUT waiting for $name intent=$want (state=$value)"; return 1
    fi
    sleep "$POLL"
  done
}

# wait_deployment NAME EXPECTED_REPLICAS TIMEOUT_S
wait_deployment() {
  local name=$1 want=$2 deadline=$(( $(date +%s) + $3 )) cur ready
  while :; do
    cur=$(kubectl get deployment "$name" -n "$NS" -o jsonpath='{.spec.replicas}' 2>/dev/null) ||
      die "cannot read deployment $name"
    ready=$(kubectl get deployment "$name" -n "$NS" -o jsonpath='{.status.readyReplicas}' 2>/dev/null) ||
      die "cannot read readiness for deployment $name"
    ready=${ready:-0}
    if [[ "$cur" == "$want" ]] && { [[ "$want" == "0" ]] || [[ "$ready" == "1" ]]; }; then
      log "$name is $want (ready=$ready)"; return 0
    fi
    if (( $(date +%s) >= deadline )); then
      log "TIMEOUT waiting for $name (want=$want cur=$cur ready=$ready)"
      return 1
    fi
    sleep "$POLL"
  done
}

pod_names() {
  local name=$1
  kubectl get pods -n "$NS" -l "app=$name" -o 'jsonpath={range .items[*]}{.metadata.name}{" "}{end}' ||
    die "cannot list pods for $name (RBAC/read failure)"
}

assert_zero_pods() {
  local name=$1 replicas pods
  replicas=$(kubectl get deployment "$name" -n "$NS" -o 'jsonpath={.spec.replicas}') ||
    die "cannot read deployment $name while fencing v14"
  [[ "$replicas" =~ ^[0-9]+$ ]] || die "$name spec.replicas is missing or invalid: '$replicas'"
  pods=$(pod_names "$name")
  if [[ "$replicas" == 0 && -z "$pods" ]]; then
    return 0
  fi
  log "$name is not fenced yet (replicas=$replicas pods=${pods:-none}; terminating pods count as present)"
  return 1
}

wait_zero_pods() {
  local name=$1 deadline=$(( $(date +%s) + DOWN_TIMEOUT ))
  while :; do
    if assert_zero_pods "$name"; then
      log "$name has replicas=0 and no pods remain"; return 0
    fi
    if (( $(date +%s) >= deadline )); then
      log "TIMEOUT waiting for $name zero-Pod fence"
      return 1
    fi
    sleep "$POLL"
  done
}

endpoint_ips() {
  kubectl get endpoints dgx-spark-backend -n "$NS" \
    -o 'jsonpath={range .subsets[*].addresses[*]}{.ip}{"\n"}{end}' ||
    die "cannot read stable Service endpoints (RBAC/read failure)"
}

wait_no_endpoints() {
  local deadline=$(( $(date +%s) + ENDPOINT_TIMEOUT )) endpoints
  while :; do
    endpoints=$(endpoint_ips)
    if [[ -z "$endpoints" ]]; then
      log "stable Service has no endpoints while v14 is fenced"; return 0
    fi
    log "waiting for stale stable Service endpoints to clear: $endpoints"
    if (( $(date +%s) >= deadline )); then
      die "stable Service still has endpoints before 1104 activation: $endpoints"
    fi
    sleep "$POLL"
  done
}

# Return one 1104 head's identity as name|IP|node|phase|Ready. Exactly one
# Running/Ready head is required before its IP may authorize the stable route.
head_pod_info() {
  local result
  result=$(kubectl get pods -n "$NS" -l 'app=glm53-flash-1104-head' \
    -o 'jsonpath={range .items[*]}{.metadata.name}{"|"}{.status.podIP}{"|"}{.spec.nodeName}{"|"}{.status.phase}{"|"}{range .status.conditions[?(@.type=="Ready")]}{.status}{end}{"\n"}{end}') ||
    die "cannot read 1104 head pod identity"
  [[ -n "$result" && "$result" != *$'\n'* ]] ||
    die "1104 must have exactly one head pod; got '${result:-none}'"
  printf '%s' "$result"
}

# Wait for one endpoint and require that it is the one Ready 1104 head Pod IP.
# Multiple addresses are never accepted, even transiently.
wait_stable_endpoint() {
  local deadline=$(( $(date +%s) + ENDPOINT_TIMEOUT )) info head_ip endpoints endpoint
  while :; do
    info=$(head_pod_info)
    IFS='|' read -r _ head_ip _ phase ready <<<"$info"
    [[ -n "$head_ip" && "$phase" == Running && "$ready" == True ]] ||
      die "1104 head is not uniquely Running/Ready with an IP: $info"
    endpoints=$(endpoint_ips)
    if [[ "$endpoints" == *$'\n'* ]]; then
      die "dgx-spark-backend has multiple endpoint addresses: $endpoints"
    fi
    endpoint=$endpoints
    if [[ -n "$endpoint" && "$endpoint" == "$head_ip" ]]; then
      log "stable endpoint is the sole Ready 1104 head ($endpoint)"
      printf '%s' "$endpoint"
      return 0
    fi
    [[ -n "$endpoint" ]] && log "stable endpoint $endpoint is not Ready 1104 head $head_ip; waiting for route convergence"
    if (( $(date +%s) >= deadline )); then
      die "TIMEOUT waiting for sole stable endpoint to match 1104 head (endpoint=${endpoint:-none} head=$head_ip)"
    fi
    sleep "$POLL"
  done
}

assert_v14_fenced() {
  local intent
  intent=$(read_intent tensorfold-v14) || die "cannot re-read v14 intent before 1104 activation"
  [[ "$intent" == 'Standby|Standby' ]] || die "v14 intent changed before 1104 activation ($intent)"
  assert_zero_pods tensorfold-v14-head || die "v14 head zero-Pod fence was lost before 1104 activation"
  assert_zero_pods tensorfold-v14-worker || die "v14 worker zero-Pod fence was lost before 1104 activation"
}

log "== preflight: require readable pool management and intents before any writes =="
pool_mode=$(read_pool_mode) || die "cannot read dgx-spark ResourcePool managementMode; refusing to patch"
[[ "$pool_mode" == Manage ]] || die "dgx-spark ResourcePool managementMode is $pool_mode, not Manage; Conductor will not actuate this cutover"
intent_1104=$(read_intent glm53-flash-1104) || die "1104 intent is unreadable, incomplete, or not a recognized state; refusing to patch"
intent_v14=$(read_intent tensorfold-v14) || die "v14 intent is unreadable, incomplete, or not a recognized state; refusing to patch"
[[ "$intent_1104" == 'Standby|Standby' ]] || die "1104 must be Standby|Standby before activation (state=$intent_1104)"
case "$intent_v14" in
  'Resident|Resident'|'Standby|Standby') ;;
  *) die "v14 intent is not a matching Resident/Standby state (state=$intent_v14)" ;;
esac
log "preflight OK: pool=Manage, v14=$intent_v14, 1104=$intent_1104"

log "== 1/5 v14 -> Standby, then require a bounded zero-Pod fence =="
if [[ "$intent_v14" != 'Standby|Standby' ]]; then
  kubectl patch managedworkload tensorfold-v14 -n "$NS" --type=merge -p '{"spec":{"desiredState":"Standby"}}' ||
    die "failed to request v14 Standby; no GLM activation attempted"
fi
wait_intent tensorfold-v14 Standby || die "v14 did not accept Standby; no GLM activation attempted"
wait_deployment tensorfold-v14-head 0 "$DOWN_TIMEOUT" || die "v14 head did not scale down"
wait_deployment tensorfold-v14-worker 0 "$DOWN_TIMEOUT" || die "v14 worker did not scale down"
wait_zero_pods tensorfold-v14-head || die "v14 head zero-Pod fence failed; no GLM activation attempted"
wait_zero_pods tensorfold-v14-worker || die "v14 worker zero-Pod fence failed; no GLM activation attempted"
assert_v14_fenced
wait_no_endpoints

log "== 2/5 GLM 1104 -> Resident (launcher self-gates on MemAvailable) =="
kubectl patch managedworkload glm53-flash-1104 -n "$NS" --type=merge -p '{"spec":{"desiredState":"Resident"}}' ||
  die "failed to request GLM 1104 Resident; v14 remains Standby"
wait_intent glm53-flash-1104 Resident || die "GLM 1104 did not accept Resident; v14 remains Standby"

log "== 3/5 waiting up to ${CUTOVER_TIMEOUT}s for both 1104 ranks (check /state/logs/rank*.log on the rank nodes) =="
# The worker is the flaky one historically; surface its restarts while waiting.
( while sleep "$WATCH_INTERVAL"; do
    w=$(kubectl get deployment glm53-flash-1104-worker -n "$NS" -o jsonpath='{.spec.replicas},{.status.readyReplicas}' 2>/dev/null || echo '?')
    h=$(kubectl get deployment glm53-flash-1104-head -n "$NS" -o jsonpath='{.spec.replicas},{.status.readyReplicas}' 2>/dev/null || echo '?')
    echo "$(date -u +%T) worker(desired,ready)=$w head(desired,ready)=$h" >&2
  done ) &
WATCH_PID=$!
trap 'kill "$WATCH_PID" 2>/dev/null || true' EXIT
wait_deployment glm53-flash-1104-worker 1 "$CUTOVER_TIMEOUT" || die "1104 worker never became ready"
wait_deployment glm53-flash-1104-head 1 "$CUTOVER_TIMEOUT" || die "1104 head never became ready"

log "== 4/5 sole stable endpoint identity + API checks =="
ip=$(wait_stable_endpoint) || die "no stable endpoint matching the sole Ready 1104 head"
curl -fsS --max-time 10 "http://$ip:8000/health" >/dev/null || die "health failed at $ip:8000"
log "health OK"
models=$(curl -fsS --max-time 10 "http://$ip:8000/v1/models") || die "/v1/models failed at $ip:8000"
echo "$models" | grep -q 'GLM-5.3-Flash-EXL3' || die "model GLM-5.3-Flash-EXL3 not in /v1/models: $models"
log "models OK"
# Re-check both pod identity and sole Service endpoint after health before the
# completion smoke; a route race is a failed cutover, not a reason to patch.
sleep "$POLL"
ip_again=$(wait_stable_endpoint) || die "stable endpoint identity failed its recheck"
[[ "$ip_again" == "$ip" ]] || die "stable endpoint changed from $ip to $ip_again during API checks"

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

log "CUTOVER COMPLETE: GLM 1104 serving at http://$ip:8000 (sole stable Service endpoint matches its Ready head)"
log "Rollback guidance: if service/API qualification degrades, do not scale manually; stop 1104 and restore v14 only through the authorized revert.sh flow."
