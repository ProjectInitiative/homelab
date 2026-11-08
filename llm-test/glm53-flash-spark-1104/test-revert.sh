#!/usr/bin/env bash
# Offline regression tests for revert.sh; all kubectl/curl calls are mocked.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/bin"
cat >"$TMP/bin/kubectl" <<'MOCK'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >>"$MOCK_CALLS"
if [[ "${MOCK_DENY_INTENT:-0}" == 1 && "$*" == get\ managedworkload* ]]; then exit 1; fi
case "$1:$2" in
  get:managedworkload)
    name=$3
    if [[ "${MOCK_MALFORMED_INTENT:-0}" == 1 ]]; then printf '|'; exit 0; fi
    if [[ "$name" == glm53-flash-1104 ]]; then
      desired=$(cat "$MOCK_STATE/1104-desired"); effective=$(cat "$MOCK_STATE/1104-effective")
    else
      desired=$(cat "$MOCK_STATE/v14-desired"); effective=$(cat "$MOCK_STATE/v14-effective")
    fi
    printf '%s|%s' "$desired" "$effective"
    ;;
  patch:managedworkload)
    name=$3
    [[ "${MOCK_FAIL_PATCH:-}" != "$name" ]] || exit 1
    if [[ "$name" == glm53-flash-1104 ]]; then
      printf Standby >"$MOCK_STATE/1104-desired"
      [[ "${MOCK_STALE_1104:-0}" == 1 ]] || printf Standby >"$MOCK_STATE/1104-effective"
    else
      printf Resident >"$MOCK_STATE/v14-desired"
      printf Resident >"$MOCK_STATE/v14-effective"
      if [[ "${MOCK_REACTIVATE_AFTER_V14:-0}" == 1 ]]; then
        printf Resident >"$MOCK_STATE/1104-desired"
        printf Resident >"$MOCK_STATE/1104-effective"
      fi
    fi
    ;;
  get:deployment)
    name=$3
    case "$name" in glm53-flash-1104-*) printf 0;; *) printf '1|1';; esac
    ;;
  get:pods)
    case "$*" in
      *'app=glm53-flash-1104-worker'*) if [[ "${MOCK_LINGERING_POD:-0}" == 1 ]]; then printf 'terminating-worker '; fi;;
      *'app=glm53-flash-1104-head'*) ;;
      *'app=tensorfold-v14-worker'*) printf 'v14-worker|172.16.4.56|chronometer|Running|True';;
      *'app=tensorfold-v14-head'*) printf 'v14-head|172.16.4.55|sextant|Running|True';;
      *) echo "unexpected pod selector: $*" >&2; exit 90;;
    esac
    ;;
  get:endpoints)
    [[ "${MOCK_ENDPOINT_MISMATCH:-0}" == 1 ]] && printf 172.16.4.99 || printf 172.16.4.55
    ;;
  *) echo "unexpected kubectl call: $*" >&2; exit 90;;
esac
MOCK
cat >"$TMP/bin/curl" <<'MOCK'
#!/usr/bin/env bash
exit 0
MOCK
chmod +x "$TMP/bin/kubectl" "$TMP/bin/curl"

setup() {
  mkdir -p "$TMP/state"
  export MOCK_STATE="$TMP/state" MOCK_CALLS="$TMP/calls" PATH="$TMP/bin:$PATH"
  : >"$MOCK_CALLS"
  printf Resident >"$TMP/state/1104-desired"; printf Resident >"$TMP/state/1104-effective"
  printf Standby >"$TMP/state/v14-desired"; printf Standby >"$TMP/state/v14-effective"
}
run_failure() {
  local expected=$1
  if printf 'CONFIRM_RING_AND_API_SMOKE\n' | env INTENT_TIMEOUT=0 DOWN_TIMEOUT=0 ENDPOINT_TIMEOUT=0 POLL_SECONDS=0 "$HERE/revert.sh" >"$TMP/failure.log" 2>&1; then
    echo "FAIL: $expected unexpectedly succeeded" >&2; exit 1
  fi
  grep -q "$expected" "$TMP/failure.log" || { cat "$TMP/failure.log" >&2; exit 1; }
}

setup
if env MOCK_STALE_1104=1 INTENT_TIMEOUT=0 DOWN_TIMEOUT=0 POLL_SECONDS=0 "$HERE/revert.sh" >"$TMP/stale.log" 2>&1; then
  echo 'FAIL: stale 1104 Standby confirmation unexpectedly succeeded' >&2; exit 1
fi
! grep -q 'patch managedworkload tensorfold-v14' "$MOCK_CALLS"
printf 'PASS failure-to-confirm-1104 blocks v14 patch\n'

setup
if "$HERE/revert.sh" >"$TMP/success.log" 2>&1; then echo 'FAIL: non-interactive run claimed complete without operator confirmation' >&2; exit 1; fi
if ! grep -q 'PROVISIONAL:' "$TMP/success.log"; then cat "$TMP/success.log" >&2; cat "$MOCK_CALLS" >&2; exit 1; fi
test "$(grep -c 'patch managedworkload glm53-flash-1104' "$MOCK_CALLS")" -eq 1
test "$(grep -c 'patch managedworkload tensorfold-v14' "$MOCK_CALLS")" -eq 1
line_1104=$(grep -n 'patch managedworkload glm53-flash-1104' "$MOCK_CALLS" | cut -d: -f1)
line_v14=$(grep -n 'patch managedworkload tensorfold-v14' "$MOCK_CALLS" | cut -d: -f1)
(( line_1104 < line_v14 ))
grep -q 'PROVISIONAL: v14 head/worker and stable endpoint health verified' "$TMP/success.log"
grep -q 'non-interactive run cannot confirm' "$TMP/success.log"
printf 'PASS recovery ordering, endpoint identity, and provisional fail-closed result\n'

setup
if env MOCK_DENY_INTENT=1 "$HERE/revert.sh" >"$TMP/denied.log" 2>&1; then echo 'FAIL: unreadable intent succeeded' >&2; exit 1; fi
! grep -q 'patch managedworkload' "$MOCK_CALLS"
printf 'PASS unreadable Conductor intent fails before writes\n'

setup
MOCK_FAIL_PATCH=glm53-flash-1104 run_failure 'failed to request 1104 Standby'
! grep -q 'patch managedworkload tensorfold-v14' "$MOCK_CALLS"
printf 'PASS 1104 patch error blocks v14 patch\n'

setup
if env MOCK_MALFORMED_INTENT=1 "$HERE/revert.sh" >"$TMP/malformed.log" 2>&1; then echo 'FAIL: malformed intent succeeded' >&2; exit 1; fi
! grep -q 'patch managedworkload' "$MOCK_CALLS"
printf 'PASS missing/malformed intent fails before writes\n'

setup
if env MOCK_LINGERING_POD=1 DOWN_TIMEOUT=0 POLL_SECONDS=0 "$HERE/revert.sh" >"$TMP/linger.log" 2>&1; then echo 'FAIL: lingering pod was ignored' >&2; exit 1; fi
! grep -q 'patch managedworkload tensorfold-v14' "$MOCK_CALLS"
grep -q 'terminating-worker' "$TMP/linger.log"
printf 'PASS lingering 1104 pod blocks v14 patch\n'

setup
if env MOCK_ENDPOINT_MISMATCH=1 POLL_SECONDS=0 "$HERE/revert.sh" >"$TMP/identity.log" 2>&1; then echo 'FAIL: wrong Service endpoint identity succeeded' >&2; exit 1; fi
grep -q 'is not Ready v14 head' "$TMP/identity.log"
printf 'PASS stable endpoint must match v14 head pod IP\n'

setup
if env MOCK_REACTIVATE_AFTER_V14=1 "$HERE/revert.sh" >"$TMP/race.log" 2>&1; then echo 'FAIL: concurrent 1104 reactivation was missed' >&2; exit 1; fi
grep -q '1104 intent changed during v14 recovery' "$TMP/race.log"
test "$(grep -c 'patch managedworkload' "$MOCK_CALLS")" -eq 2
printf 'PASS concurrent 1104 reactivation detected without corrective writes\n'
