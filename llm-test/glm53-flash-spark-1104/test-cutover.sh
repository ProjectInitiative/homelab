#!/usr/bin/env bash
# Offline regression tests for cutover.sh; all kubectl/curl calls are mocked.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/bin"
cat >"$TMP/bin/kubectl" <<'MOCK'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >>"$MOCK_CALLS"
case "$1:$2" in
  get:resourcepool)
    [[ "${MOCK_DENY_POOL:-0}" != 1 ]] || exit 1
    printf '%s' "${MOCK_POOL_MODE:-Manage}"
    ;;
  get:managedworkload)
    [[ "${MOCK_DENY_INTENT:-0}" != 1 ]] || exit 1
    name=$3
    if [[ "${MOCK_MALFORMED_INTENT:-0}" == 1 ]]; then printf '|'; exit 0; fi
    if [[ "$name" == glm53-flash-1104 ]]; then
      if [[ "${MOCK_1104_INITIAL_RESIDENT:-0}" == 1 ]]; then
        desired=Resident; effective=Resident
      else
        desired=$(cat "$MOCK_STATE/1104-desired"); effective=$(cat "$MOCK_STATE/1104-effective")
      fi
      state_prefix=1104
    else
      desired=$(cat "$MOCK_STATE/v14-desired"); effective=$(cat "$MOCK_STATE/v14-effective")
      state_prefix=v14
    fi
    transition="$MOCK_STATE/$state_prefix-transition"
    if [[ "${MOCK_TRANSITIONAL_INTENT:-0}" == 1 && -f "$transition" ]]; then
      if [[ "$(cat "$transition")" == 0 ]]; then
        printf 1 >"$transition"
      else
        if [[ "$state_prefix" == 1104 ]]; then effective=Resident; else effective=Standby; fi
      fi
    fi
    printf '%s|%s' "$desired" "$effective"
    ;;
  patch:managedworkload)
    name=$3
    printf '%s' patched >"$MOCK_STATE/$name-patched"
    [[ "${MOCK_FAIL_PATCH:-}" != "$name" ]] || exit 1
    if [[ "$name" == tensorfold-v14 ]]; then
      printf Standby >"$MOCK_STATE/v14-desired"
      if [[ "${MOCK_TRANSITIONAL_INTENT:-0}" == 1 ]]; then
        printf Resident >"$MOCK_STATE/v14-effective"
        printf 0 >"$MOCK_STATE/v14-transition"
      else
        printf Standby >"$MOCK_STATE/v14-effective"
      fi
    else
      printf Resident >"$MOCK_STATE/1104-desired"
      if [[ "${MOCK_TRANSITIONAL_INTENT:-0}" == 1 ]]; then
        printf Standby >"$MOCK_STATE/1104-effective"
        printf 0 >"$MOCK_STATE/1104-transition"
      else
        printf Resident >"$MOCK_STATE/1104-effective"
      fi
    fi
    ;;
  get:deployment)
    name=$3
    case "$name" in
      tensorfold-v14-*) printf 0 ;;
      glm53-flash-1104-*) printf 1 ;;
      *) echo "unexpected deployment: $*" >&2; exit 90 ;;
    esac
    ;;
  get:pods)
    case "$*" in
      *'app=tensorfold-v14-head'*)
        [[ "${MOCK_LINGERING_V14:-0}" == 1 ]] && printf 'terminating-head '
        ;;
      *'app=tensorfold-v14-worker'*)
        [[ "${MOCK_LINGERING_V14:-0}" == 1 ]] && printf 'terminating-worker '
        ;;
      *'app=glm53-flash-1104-head'*)
        printf '1104-head|172.16.4.55|sextant|Running|True'
        ;;
      *'app=glm53-flash-1104-worker'*)
        printf '1104-worker|172.16.4.56|chronometer|Running|True'
        ;;
      *) echo "unexpected pod selector: $*" >&2; exit 90 ;;
    esac
    ;;
  get:endpoints)
    if [[ ! -f "$MOCK_STATE/glm53-flash-1104-patched" ]]; then
      [[ "${MOCK_STALE_ENDPOINT:-0}" != 1 ]] || printf '172.16.4.44'
    elif [[ "${MOCK_ENDPOINT_MODE:-match}" == mismatch ]]; then
      printf '172.16.4.99'
    elif [[ "${MOCK_ENDPOINT_MODE:-match}" == multiple ]]; then
      printf '172.16.4.55\n172.16.4.56\n'
    else
      printf '172.16.4.55'
    fi
    ;;
  *) echo "unexpected kubectl call: $*" >&2; exit 90 ;;
esac
MOCK
cat >"$TMP/bin/curl" <<'MOCK'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >>"$MOCK_CURL_CALLS"
case "$*" in
  *'/v1/models'*) printf '{"data":[{"id":"GLM-5.3-Flash-EXL3"}]}' ;;
  *'chat/completions'*) printf '{"choices":[{"message":{"content":"ready"}}]}' ;;
esac
MOCK
chmod +x "$TMP/bin/kubectl" "$TMP/bin/curl"

setup() {
  mkdir -p "$TMP/state"
  export MOCK_STATE="$TMP/state" MOCK_CALLS="$TMP/calls" MOCK_CURL_CALLS="$TMP/curl-calls" PATH="$TMP/bin:$PATH"
  : >"$MOCK_CALLS"; : >"$MOCK_CURL_CALLS"
  rm -f "$TMP/state"/*-patched "$TMP/state"/*-transition
  printf Standby >"$TMP/state/1104-desired"; printf Standby >"$TMP/state/1104-effective"
  printf Resident >"$TMP/state/v14-desired"; printf Resident >"$TMP/state/v14-effective"
}
run_cutover() {
  env CUTOVER_TIMEOUT=0 DOWN_TIMEOUT=0 ENDPOINT_TIMEOUT=0 INTENT_TIMEOUT=1 POLL=0 WATCH_INTERVAL=60 "$@" "$HERE/cutover.sh"
}
run_failure() {
  local expected=$1; shift
  if env CUTOVER_TIMEOUT=0 DOWN_TIMEOUT=0 ENDPOINT_TIMEOUT=0 INTENT_TIMEOUT=0 POLL=0 WATCH_INTERVAL=60 "$@" "$HERE/cutover.sh" >"$TMP/failure.log" 2>&1; then
    echo "FAIL: $expected unexpectedly succeeded" >&2; exit 1
  fi
  grep -q "$expected" "$TMP/failure.log" || { cat "$TMP/failure.log" >&2; exit 1; }
}

setup
run_failure 'managementMode is Observe' MOCK_POOL_MODE=Observe
! grep -q 'patch managedworkload' "$MOCK_CALLS"
printf 'PASS Observe pool fails before writes\n'

setup
run_failure 'cannot read dgx-spark ResourcePool' MOCK_DENY_POOL=1
! grep -q 'patch managedworkload' "$MOCK_CALLS"
printf 'PASS unreadable pool fails before writes\n'

setup
run_failure '1104 intent is unreadable' MOCK_DENY_INTENT=1
! grep -q 'patch managedworkload' "$MOCK_CALLS"
printf 'PASS unreadable intents fail before writes\n'

setup
run_failure '1104 must be Standby' MOCK_1104_INITIAL_RESIDENT=1
! grep -q 'patch managedworkload' "$MOCK_CALLS"
printf 'PASS non-Standby 1104 intent fails before writes\n'

setup
run_failure 'zero-Pod fence failed' MOCK_LINGERING_V14=1
! grep -q 'patch managedworkload glm53-flash-1104' "$MOCK_CALLS"
printf 'PASS terminating v14 Pod blocks 1104 activation\n'

setup
run_failure 'stable Service still has endpoints' MOCK_STALE_ENDPOINT=1
! grep -q 'patch managedworkload glm53-flash-1104' "$MOCK_CALLS"
printf 'PASS stale stable endpoint blocks 1104 activation\n'

setup
run_failure 'multiple endpoint addresses' MOCK_ENDPOINT_MODE=multiple
if ! grep -q 'patch managedworkload glm53-flash-1104' "$MOCK_CALLS"; then
  echo 'FAIL: endpoint test did not reach 1104 activation' >&2; exit 1
fi
printf 'PASS multiple stable endpoints fail closed after activation\n'

setup
run_failure 'not Ready 1104 head' MOCK_ENDPOINT_MODE=mismatch
printf 'PASS stable endpoint identity mismatch fails closed\n'

setup
if ! run_cutover MOCK_TRANSITIONAL_INTENT=1 >"$TMP/success.log" 2>&1; then
  cat "$TMP/success.log" >&2
  exit 1
fi
line_v14=$(grep -n 'patch managedworkload tensorfold-v14' "$MOCK_CALLS" | cut -d: -f1)
line_1104=$(grep -n 'patch managedworkload glm53-flash-1104' "$MOCK_CALLS" | cut -d: -f1)
(( line_v14 < line_1104 ))
grep -q 'sole stable Service endpoint matches its Ready head' "$TMP/success.log"
grep -q 'http://172.16.4.55:8000' "$MOCK_CURL_CALLS"
if grep -qE '^[0-9]{4}-[0-9]{2}-[0-9]{2}T' "$MOCK_CURL_CALLS"; then
  echo 'FAIL: endpoint capture included log output' >&2; exit 1
fi
printf 'PASS cutover ordering, endpoint identity/recheck, and clean endpoint capture\n'
