#!/usr/bin/env bash
# Verify argo VM JuiceFS mounts use the nocache config.
# Run from a machine with kubectl + jq and an auth k8s session (context "mc").
set -u
CTX="${KUBE_CONTEXT:-mc}"

echo "=== 1. ConfigMap patch landed ==="
kubectl --context "$CTX" -n kube-system get configmap juicefs-csi-driver-config -o json \
  | jq -r '.data | to_entries[].value' | grep -B1 -A6 'argo-'

echo
echo "=== 2. All JuiceFS mount pods and their cache args ==="
kubectl --context "$CTX" -n kube-system get pods -o json \
  | jq -r '.items[]
      | select(.metadata.name | startswith("juicefs-"))
      | select((.metadata.name | test("argo")) or true)
      | .metadata.name + " :: " + ([.spec.containers[].args[]? // empty] | join(" "))' \
  | sort

echo
echo "=== 3. PV names for argo PVCs ==="
ROOT_PV=$(kubectl --context "$CTX" -n argo get pvc argo-root -o jsonpath='{.spec.volumeName}')
DATA_PV=$(kubectl --context "$CTX" -n argo get pvc argo-data -o jsonpath='{.spec.volumeName}')
echo "argo-root -> $ROOT_PV"
echo "argo-data -> $DATA_PV"

echo
echo "=== 4. Mount pods for argo volumes: full mount command (expect cache-size=0, prefetch=0, no cache-dir) ==="
for pv in "$ROOT_PV" "$DATA_PV"; do
  kubectl --context "$CTX" -n kube-system get pods -o json \
    | jq -r --arg pv "$pv" '.items[]
        | select(.metadata.name | contains($pv))
        | .metadata.name as $n
        | ( [.spec.containers[].command[]? // empty] + [.spec.containers[].args[]? // empty] + ([.spec.containers[].env[]? | (.name + "=" + (.value // ""))]) ) | join(" ")
        | $n + "\n    " + .' | grep -E '^(juicefs|    )' | grep -E "^juicefs|cache-size|prefetch|cache-dir|mount"
done

echo
echo "=== 5. PVC status ==="
kubectl --context "$CTX" -n argo get pvc -o json \
  | jq -r '.items[] | .metadata.name + " :: phase=" + .status.phase + " :: sc=" + (.spec.storageClassName // "")'
