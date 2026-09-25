# RDMA shared device plugin

This app makes the DGX Spark ConnectX Ethernet/RoCE devices schedulable through
the extended resource `rdma/hca_shared_devices`.

The DaemonSet selects nodes by the existing `gpu=dgx-spark` capability label,
not by hostname. It discovers Mellanox (`15b3`) Ethernet devices driven by
`mlx5_core`. `rdmaHcaMax: 1` intentionally permits one RDMA-consuming workload
per Spark, matching the single `nvidia.com/gpu` resource on each node.

The accompanying `nvidia-rdma` RuntimeClass uses the NVIDIA container runtime
and adds the stable Spark fabric scheduling contract. Workloads therefore do
not need hostname affinity or physical-interface selectors:

```yaml
runtimeClassName: nvidia-rdma
resources:
  limits:
    nvidia.com/gpu: 1
    rdma/hca_shared_devices: 1
```

The matching node labels are registered by the shared DGX Spark NixOS module:

```text
fabric.homelab.io/rdma=roce-v2
fabric.homelab.io/topology=direct-ring
```

That module also materializes `/var/lib/dgx-spark/rdma-fabric.json` on every Spark.
It contains the local node's control-plane address and a stable link inventory
(`id`, `peerNode`, interface, local/peer addresses, and MACs). A workload that
needs topology-specific launch logic can mount the same path on every node:

```yaml
volumes:
  - name: rdma-fabric
    hostPath:
      path: /var/lib/dgx-spark/rdma-fabric.json
      type: File
```

This keeps physical addresses in the Nix host inventory rather than duplicating
them in model manifests. Generic workloads should also obtain their placement
identity from the Downward API:

```yaml
env:
  - name: NODE_NAME
    valueFrom:
      fieldRef:
        fieldPath: spec.nodeName
  - name: HOST_IP
    valueFrom:
      fieldRef:
        fieldPath: status.hostIP
```

Use a headless Service name for distributed rendezvous and required hostname
anti-affinity for one rank per Spark. Do not turn every listed HCA into one
unconditional `NCCL_IB_HCA` value: each direct-link subnet reaches one peer, so
the recipe-specific launcher must choose the peer-correct link set.

The plugin exposes and accounts for RDMA character devices; it does not create
a pod network interface or IP address. Existing `hostNetwork` workloads can use
it immediately for scheduling/accounting. Their rendezvous address should use
Kubernetes DNS or the common Kubernetes network, while NCCL uses the host-owned
RoCE links. Removing `hostNetwork` requires a reviewed secondary-network design
and is deliberately out of scope because the three-Spark direct-link fabric
uses different point-to-point subnets per node pair.

Source: `Mellanox/k8s-rdma-shared-dev-plugin` v1.5.3. The image is pinned to the
multi-architecture manifest digest.

## Rollout order

1. Deploy the shared DGX Spark NixOS module to all three nodes. This creates the
   inventory and registers the fabric labels.
2. Verify the labels are present. K3s may preserve the labels from the node's
   original registration; if an existing Node was not updated, reconcile them
   once through the Kubernetes API:

   ```bash
   kubectl label nodes -l gpu=dgx-spark \
     fabric.homelab.io/rdma=roce-v2 \
     fabric.homelab.io/topology=direct-ring --overwrite
   ```

3. Sync this Argo CD app and verify every Spark advertises both
   `nvidia.com/gpu` and `rdma/hca_shared_devices`.
4. Run the suspended smoke job below.

## Qualification smoke job

`smoke/` contains a suspended three-pod Job. It requests one GPU and one RDMA
allocation per pod and uses required hostname anti-affinity, so unsuspending it
validates all three Sparks without embedding their names. It checks GPU/RDMA
devices, the inventory schema, control address, MTU, link state, netdev-to-HCA
mapping, local addresses, and permanent peer neighbors. It does not attempt to
select NCCL rails or qualify TP=3.

After the Nix host changes and this plugin are deployed:

```bash
kubectl apply -k bootstrap/base/rdma-shared-device-plugin/smoke
kubectl patch job -n kube-system rdma-fabric-smoke \
  --type=merge -p '{"spec":{"suspend":false}}'
kubectl logs -n kube-system -l app.kubernetes.io/name=rdma-fabric-smoke \
  --prefix --tail=-1
kubectl delete -k bootstrap/base/rdma-shared-device-plugin/smoke
```
