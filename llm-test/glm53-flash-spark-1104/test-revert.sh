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
    if [[ "$name" == glm53-flash-1104 ]]; then
      desired=$(cat "$MOCK_STATE/1104-desired"); effective=$(cat "$MOCK_STATE/1104-effective")
    else
      desired=$(cat "$MOCK_STATE/v14-desired"); effective=$(cat "$MOCK_STATE/v14-effective")
    fi
    case "$*" in *'.spec.desiredState'*) printf '%s|%s' "$desired" "$effective";; *) exit 2;; esac
    ;;
  patch:managedworkload)
    name=$3
    if [[ "$name" == glm53-flash-1104 ]]; then
      printf Standby >"$MOCK_STATE/1104-desired"
      [[ "${MOCK_STALE_1104:-0}" == 1 ]] || printf Standby >"$MOCK_STATE/1104-effective"
    else
      printf Resident >"$MOCK_STATE/v14-desired"
      printf Resident >"$MOCK_STATE/v14-effective"
    fi
    ;;
  get:deployment)
    name=$3
    case "$name" in glm53-flash-1104-*) printf 0;; *) printf '1|1';; esac
    ;;
  get:pods) ;;
  get:endpoints) printf 172.16.4.55;;
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

setup
if MOCK_STALE_1104=1 INTENT_TIMEOUT=0 "$HERE/revert.sh" >"$TMP/stale.log" 2>&1; then
  echo 'FAIL: stale 1104 Standby confirmation unexpectedly succeeded' >&2; exit 1
fi
if grep -q 'patch managedworkload tensorfold-v14' "$MOCK_CALLS"; then
  echo 'FAIL: v14 was requested before 1104 Standby confirmation' >&2; exit 1
fi
printf 'PASS failure-to-confirm-1104 blocks v14 patch\n'

setup
"$HERE/revert.sh" >"$TMP/success.log" 2>&1
test "$(grep -c 'patch managedworkload glm53-flash-1104' "$MOCK_CALLS")" -eq 1
test "$(grep -c 'patch managedworkload tensorfold-v14' "$MOCK_CALLS")" -eq 1
line_1104=$(grep -n 'patch managedworkload glm53-flash-1104' "$MOCK_CALLS" | cut -d: -f1)
line_v14=$(grep -n 'patch managedworkload tensorfold-v14' "$MOCK_CALLS" | cut -d: -f1)
(( line_1104 < line_v14 ))
grep -q 'has replicas=0 and no pods remain' "$TMP/success.log"
grep -q 'REVERT COMPLETE' "$TMP/success.log"
printf 'PASS success ordering and endpoint health\n'

setup
if MOCK_DENY_INTENT=1 "$HERE/revert.sh" >"$TMP/denied.log" 2>&1; then
  echo 'FAIL: unreadable Conductor intent unexpectedly succeeded' >&2; exit 1
fi
if grep -q 'patch managedworkload' "$MOCK_CALLS"; then
  echo 'FAIL: script wrote after Conductor intent read denial' >&2; exit 1
fi
printf 'PASS unreadable Conductor intent fails before writes\n'
