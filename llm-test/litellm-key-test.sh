#!/usr/bin/env bash
# Validate a LiteLLM virtual key against the prod gateway:
#   1. Which models the key can see (/v1/models is allowlist-filtered per key)
#   2. A real completion smoke on every visible model
#   3. Deny checks: named sensitive models must be refused
#   4. Admin-surface checks: a scoped key must not manage keys/users/spend
#
# Usage:   litellm-key-test.sh <sk-key> [expect-denied-model ...]
# Example: litellm-key-test.sh sk-XXXX codex gpt-6-sol openai-codex
# Env:     BASE (default http://ai.taildeab2.ts.net)
set -u
KEY="${1:?usage: litellm-key-test.sh <sk-key> [expect-denied-model ...]}"; shift
BASE="${BASE:-http://ai.taildeab2.ts.net}"

echo "== endpoint: $BASE"
echo
echo "== models visible to this key (this IS the allowlist):"
MODELS=$(curl -sS --max-time 15 -H "Authorization: Bearer $KEY" "$BASE/v1/models" | jq -r '.data[].id' 2>/dev/null)
if [ -z "$MODELS" ]; then
  echo "  (none — key invalid, or allowed_models excludes everything)"
else
  echo "$MODELS" | sed 's/^/  /'
fi
echo

echo "== completion smoke on visible models (expect 200):"
for m in $MODELS; do
  code=$(curl -s -o /tmp/ltc.$$ -w '%{http_code}' --max-time 90 -X POST "$BASE/v1/chat/completions" \
    -H "Authorization: Bearer $KEY" -H 'Content-Type: application/json' \
    -d "{\"model\":\"$m\",\"messages\":[{\"role\":\"user\",\"content\":\"reply with the single word: pong\"}],\"max_tokens\":5}")
  if [ "$code" = 200 ]; then verdict="OK"; else verdict="UNEXPECTED (check body)"; fi
  echo "  [$code] $m — $verdict $(head -c 140 /tmp/ltc.$$ | tr -d '\n')"
  rm -f /tmp/ltc.$$
done
echo

echo "== deny checks (expect non-200 on every line):"
if [ $# -eq 0 ]; then
  echo "  (none passed — rerun with sensitive model names, e.g.: codex gpt-6-sol)"
fi
for m in "$@"; do
  code=$(curl -s -o /tmp/ltd.$$ -w '%{http_code}' --max-time 30 -X POST "$BASE/v1/chat/completions" \
    -H "Authorization: Bearer $KEY" -H 'Content-Type: application/json' \
    -d "{\"model\":\"$m\",\"messages\":[{\"role\":\"user\",\"content\":\"ping\"}],\"max_tokens\":5}")
  if [ "$code" = 200 ]; then
    echo "  [$code] $m — FAIL: MODEL IS ACCESSIBLE"
    rm -f /tmp/ltd.$$
  else
    echo "  [$code] $m — blocked: $(head -c 140 /tmp/ltd.$$ | tr -d '\n')"
    rm -f /tmp/ltd.$$
  fi
done
echo

echo "== admin surface (expect non-200 on every line):"
for ep in /v1/key/info /spend /user/info; do
  code=$(curl -s -o /tmp/lta.$$ -w '%{http_code}' --max-time 15 -H "Authorization: Bearer $KEY" "$BASE$ep")
  echo "  [$code] GET $ep"
  rm -f /tmp/lta.$$
done
