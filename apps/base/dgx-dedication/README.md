# DGX dedication

This change prepares the DGX Spark workloads for a dedicated node taint. It
addresses RISK-0044-class instability and the 2026-11-11 05:07Z chronometer
memcg OOM kill of `juicefs/mount.juicefs` during model-cache read storms.

## Ordered rollout

1. Merge this PR and wait for the Argo sync to complete. The v14 manifests are
   applied manually, not via Argo; apply those manifests through the existing
   manual v14 runbook after the sync.
2. Quiesce every active serving lane using `model-cache` before touching its
   mount pods. Do not delete mount pods while TensorFold/FUSE consumers are
   active: the documented failure mode is CSI replacement loops,
   `function timeout`, `mount point is not ready in 60s`, and `transport
   endpoint is not connected`.
3. Identify only the model-cache JuiceFS mount pods (the CSI label is
   `app.kubernetes.io/name=juicefs-mount`). Expect one mount pod per DGX node
   (three currently). If the label selector returns none, use the `juicefs-`
   name-prefix fallback from `tools/verify-argo-nocache.sh`:

   ```sh
   kubectl --context mc get pods -A -l app.kubernetes.io/name=juicefs-mount -o wide
   kubectl --context mc get pods -A -o wide | grep 'juicefs-'
   ```

4. Delete the identified model-cache mount pod names, then wait for CSI to
   recreate them:

   ```sh
   kubectl --context mc -n <namespace> delete pod <model-cache-mount-pod>...
   ```

   Mount Pods must be recreated for option changes to take
   effect; this is also why the `model-cache` mount patch remains last in the
   cluster values.
5. Verify the recreated mount pod spec carries the memory headroom:

   ```sh
   kubectl --context mc get pods -A -l app.kubernetes.io/name=juicefs-mount -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,NODE:.spec.nodeName,CPU_REQ:.spec.containers[*].resources.requests.cpu,MEM_REQ:.spec.containers[*].resources.requests.memory,CPU_LIMIT:.spec.containers[*].resources.limits.cpu,MEM_LIMIT:.spec.containers[*].resources.limits.memory'
   ```

6. Before tainting, verify every JuiceFS mount pod's node and tolerations:

   ```sh
   kubectl --context mc get pods -A -l app.kubernetes.io/name=juicefs-mount -o jsonpath='{range .items[*]}{.metadata.namespace}{"/"}{.metadata.name}{" node="}{.spec.nodeName}{" tolerations="}{.spec.tolerations}{"\n"}{end}'
   ```

   Submariner's route-agent must also tolerate the taint; verify its
   tolerations with JSONPath and extend the chart values before tainting if
   `operator: Exists` is absent:

   ```sh
   kubectl --context mc get pods -A -o jsonpath='{range .items[*]}{.metadata.namespace}{"/"}{.metadata.name}{" tolerations="}{.spec.tolerations}{"\n"}{end}' | grep -i routeagent
   ```

7. After the mount-pod and route-agent checks pass, taint the DGX nodes:

   ```sh
   kubectl --context mc taint nodes sextant chronometer octant dgx-spark-dedicated=true:NoSchedule
   ```

8. Restore the quiesced resident lane and verify post-taint readiness for both
   the lane pods and the JuiceFS mount pods:

   ```sh
   kubectl --context mc -n llm-test wait --for=condition=Ready pod -l lane=<resident-lane> --timeout=10m
   kubectl --context mc -n llm-test get pods -l lane=<resident-lane> -o wide
   kubectl --context mc wait --for=condition=Ready pod -A -l app.kubernetes.io/name=juicefs-mount --timeout=10m
   kubectl --context mc get pods -A -l app.kubernetes.io/name=juicefs-mount -o wide
   kubectl --context mc get pods -A -l app.kubernetes.io/name=juicefs-mount -o jsonpath='{range .items[*]}{.metadata.namespace}{"/"}{.metadata.name}{" node="}{.spec.nodeName}{" tolerations="}{.spec.tolerations}{"\n"}{end}'
   ```

Generic pods (`ai-proxy-test`, `conductor-controller`, `forgejo-runner`,
ingress, OpenBao snapshot jobs, and `svclb`) cannot tolerate the taint and
cannot be rescheduled onto DGX nodes. The pinned `forgejo-runner-arm` on
sextant is a deliberate DGX-resident exception and has the matching
`toleration`. `svclb` load-balancer VIPs will simply stop routing via DGX nodes;
this is acceptable because the Garage, Postgres, and Samba VIPs live elsewhere.

To roll back the taint:

```sh
kubectl --context mc taint nodes sextant chronometer octant dgx-spark-dedicated:NoSchedule-
```
