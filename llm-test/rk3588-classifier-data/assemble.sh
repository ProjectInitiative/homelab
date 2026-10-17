#!/usr/bin/env bash
# Assemble rkcls v1 training data: verify locally with the regex frontline,
# upload gen/*.jsonl to the model-cache PVC, publish the SFT code ConfigMap.
# Usage: ./assemble.sh [--upload-only]
set -euo pipefail
cd "$(dirname "$0")"
NS=llm-test
GEN=gen
UPLOAD=${1:-}

echo "== 1. local regex verification =="
python3 - <<'PY'
import json, sys, pathlib
sys.path.insert(0, '.')
from sec_scan import scan
ok = True
for p in sorted(pathlib.Path('gen').glob('*.jsonl')):
    rows = [json.loads(l) for l in p.open() if l.strip()]
    flagged = [r for r in rows if scan(r['content'])['flag']]
    exp_flag = [r for r in rows if r['expected'] == 'flag']
    print(f"{p.name}: {len(rows)} rows | {len(exp_flag)} flag-expected | regex flags {len(flagged)}")
    if p.stem.startswith('secrets'):
        bad = [r['id'] for r in exp_flag if not scan(r['content'])['flag']]
        if bad:
            ok = False
            print(f"  VIOLATION: {len(bad)} secret rows not regex-flagged: {bad[:8]}")
    else:
        leaked = [(r['id'], r['category']) for r in rows
                  if r['expected'] == 'pass' and scan(r['content'])['flag']]
        if leaked:
            print(f"  note: {len(leaked)} pass rows regex-flagged (review these): {leaked[:8]}")
if not ok:
    sys.exit("fix secret rows before uploading")
PY

[ "$UPLOAD" = "--upload-only" ] || true

echo "== 2. upload gen/ + spec to PVC =="
kubectl -n "$NS" delete pod rkcls-uploader --ignore-not-found --wait=false >/dev/null 2>&1 || true
kubectl -n "$NS" run rkcls-uploader --restart=Never --image=busybox:stable \
  --overrides '{"spec":{"containers":[{"name":"up","image":"busybox:stable","command":["sleep","3600"],"volumeMounts":[{"name":"data","mountPath":"/data"}]}],"volumes":[{"name":"data","persistentVolumeClaim":{"claimName":"model-cache"}}]}}' >/dev/null
kubectl -n "$NS" wait --for=condition=Ready pod/rkcls-uploader --timeout=90s >/dev/null
kubectl -n "$NS" exec rkcls-uploader -- mkdir -p /data/rkcls/gen
for f in "$GEN"/*.jsonl DATA-SPEC.md; do
  gzip -c "$f" | base64 -w0 | kubectl -n "$NS" exec -i rkcls-uploader -- \
    sh -c "base64 -d | gunzip > /data/rkcls/$f"
  echo "  uploaded $f"
done
kubectl -n "$NS" delete pod rkcls-uploader --wait=false >/dev/null

echo "== 3. publish SFT code + eval-corpus ConfigMaps =="
CORPUS=../../experiments/cygnet-bench/corpus
kubectl create configmap rkcls-sft-code -n "$NS" \
  --from-file=sft_train.py=train/sft_train.py \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl create configmap rkcls-eval-corpus -n "$NS" \
  --from-file=prompts.jsonl="$CORPUS/prompts.jsonl" \
  --from-file=edge_cases.jsonl="$CORPUS/edge_cases.jsonl" \
  --from-file=injection.jsonl="$CORPUS/injection.jsonl" \
  --dry-run=client -o yaml | kubectl apply -f -
echo "== done. unsuspend the training job when ready: kubectl -n $NS patch job rkcls-sft-v1 --type=merge -p '{\"spec\":{\"suspend\":false}}' =="

# (rkcls-eval-corpus configmap is published alongside the code CM)
