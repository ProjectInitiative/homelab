#!/usr/bin/env bash
# Diagnose why virt-launcher-argo is stuck in Init:0/1.
# Run from an auth k8s session (context "mc").
set -u
CTX="${KUBE_CONTEXT:-mc}"
NS="${ARGO_NS:-argo}"
POD="${POD:-$(kubectl --context "$CTX" -n "$NS" get pods -l kubevirt.io/vm=argo -o jsonpath='{.items[0].metadata.name}')}"

echo "pod=$POD"

echo
echo "=== 1. Pod init containers status ==="
kubectl --context "$CTX" -n "$NS" get pod "$POD" -o json \
  | jq -r '.status.initContainerStatuses[]? | .name + " :: state=" + ((.state.waiting.reason // .state.running.startedAt // .state.terminated.reason) | tostring) + " :: " + (.state.waiting.message // .state.terminated.message // "")'

echo
echo "=== 2. Events for the pod ==="
kubectl --context "$CTX" -n "$NS" get events --field-selector involvedObject.name="$POD" --sort-by=.lastTimestamp -o json \
  | jq -r '.items[] | [.lastTimestamp,.reason,.message] | @tsv' | tail -30

echo
echo "=== 3. DataVolume / import status ==="
kubectl --context "$CTX" -n "$NS" get datavolumes -o wide 2>/dev/null
kubectl --context "$CTX" -n "$NS" get pvc -o json \
  | jq -r '.items[] | .metadata.name + " :: " + .status.phase + " :: " + (.metadata.annotations["cdi.kubevirt.io/storage.pod.phase"] // "no-importer-annotation")'

echo
echo "=== 4. CDI importer pods + logs ==="
kubectl --context "$CTX" -n "$NS" get pods -l cdi.kubevirt.io=importer 2>/dev/null
for p in $(kubectl --context "$CTX" -n "$NS" get pods -l cdi.kubevirt.io=importer -o name 2>/dev/null); do
  echo "--- $p (importer) ---"
  kubectl --context "$CTX" -n "$NS" logs "$p" -c importer --tail=40 2>&1 | tail -40
done

echo
echo "=== 5. Init container logs (all init containers) ==="
INITS=$(kubectl --context "$CTX" -n "$NS" get pod "$POD" -o json | jq -r '.spec.initContainers[].name')
for c in $INITS; do
  echo "--- init container: $c ---"
  kubectl --context "$CTX" -n "$NS" logs "$POD" -c "$c" --tail=40 2>&1 | tail -40
done

echo
echo "=== 6. argo-s3-creds secret present? (metadata only) ==="
kubectl --context "$CTX" -n "$NS" get secret argo-s3-creds -o jsonpath='{.metadata.name} keys={.data}' 2>&1 | cut -c1-120; echo

echo
echo "=== 7. Garage reachable from cluster? ==="
kubectl --context "$CTX" -n garage get svc -o wide 2>/dev/null | head -5
kubectl --context "$CTX" -n argo run --rm -i --restart=Never garage-probe --image=curlimages/curl:latest --command -- curl -sS -o /dev/null -w '%{http_code}\n' --max-time 8 http://us-east-1.garage.svc.cluster.local:3900/ 2>&1 | tail -3
