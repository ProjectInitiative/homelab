# JuiceFS CSI registration incident postmortem

Status: mitigated; GitOps reconciliation and migration cleanup still required  
Incident date: 2026-10-28  
Affected cluster: `mc`  
Affected namespace/workload: `llm-test/ai-proxy`

## Summary

The AI proxy pods appeared to fail because their existing `juicefs-sc` PVC could
not be mounted on replacement pods. The PVC and PV were still `Bound` and their
StorageClass had not changed.

The actual failure was that the cluster-scoped resource
`CSIDriver/csi.juicefs.com` was missing. Without that resource, Kubernetes did
not know that JuiceFS is a non-attaching CSI driver. It treated the volume as
requiring an external CSI attacher, but the JuiceFS controller did not run an
external attacher sidecar. New `VolumeAttachment` objects remained
`attached=false` until kubelet timed out.

The JuiceFS node pods were also unstable during the incident. Restarting the
node DaemonSet restored the node sockets and `CSINode` entries, but did not fix
the missing `CSIDriver` object or stale unattached `VolumeAttachment` objects.

## Impact

- `ai-proxy` remained at `1/2` ready.
- Replacement pods were stuck in `ContainerCreating` or failed with
  `FailedAttachVolume` / `FailedMount`.
- Other JuiceFS consumers, including model-cache workloads, showed the same
  external-attacher timeout.
- Existing pods could continue using an already-mounted filesystem, which made
  the PVC look healthy while new mounts failed.
- After storage recovery, one new LiteLLM pod separately spent too long in
  startup because its ChatGPT refresh token returned HTTP 401. That was a
  distinct application credential issue, not a storage issue.

## Timeline and evidence

1. `litellm-chatgpt-tokens` remained bound to PV
   `pvc-eca4ccd6-0469-4d91-9ab3-0f7820bc2c87` through the incident.
2. The replacement pod on another node generated:
   `driver name csi.juicefs.com not found in the list of registered CSI drivers`
   and later:
   `timed out waiting for external-attacher of csi.juicefs.com`.
3. `juicefs-csi-node` pods had repeated restarts and mount pods had
   `FailedKillPod` errors with `DeadlineExceeded` while stopping FUSE mounts.
4. `CSINode` objects still listed `csi.juicefs.com`, but that was stale node
   registration state and did not prove that `CSIDriver/csi.juicefs.com`
   existed.
5. `kubectl get csidriver csi.juicefs.com` returned `NotFound`.
6. The repository already contained the required manifest:
   `bootstrap/base/juicefs-platform/csidriver.yaml`:

   ```yaml
   spec:
     attachRequired: false
     podInfoOnMount: true
   ```

7. Applying that existing manifest and removing unattached stale JuiceFS
   `VolumeAttachment` objects allowed the replacement proxy pod to mount the
   PVC. The original proxy returned to `2/2` ready.

## Contributing factors

### 1. Ad hoc migration changes expanded the blast radius

The working tree contained uncommitted migration additions:

- `juicefs-cache-sc`
- `model-cache-ephemeral`
- `juicefs-format-cache`
- `model-cache-migrate-to-ephemeral`
- a change to the global `ceMountImage` used by the DGX cache-ring mount policy

The new cache PVC used `juicefs-cache-sc`, not the AI proxy's existing
`juicefs-sc`. Its migration Job never started because it was unschedulable on
`octant` due to insufficient CPU. Therefore the migration did not move data,
but it introduced new cluster state while the shared CSI system was already
fragile.

The cache-image change also modified a shared JuiceFS mount policy rather than
being isolated to a disposable test resource. This caused mount-pod churn and
increased the consequences of the CSI registration/cleanup problem.

The evidence does not prove that creating the new StorageClass directly deleted
the `CSIDriver` object. The stronger conclusion is that the ad hoc changes
exposed a GitOps ownership/reconciliation gap: a required cluster-scoped
resource existed in Git but was absent from the cluster.

### 2. Shared-resource ownership was ambiguous

`CSIDriver/csi.juicefs.com` is represented under
`bootstrap/base/juicefs-platform/csidriver.yaml`, while the JuiceFS CSI Helm
application also manages the CSI installation. The existing documentation
already records an Argo shared-resource warning for this object.

A cluster-scoped resource with ambiguous ownership can be deleted, skipped, or
left drifted without the workload-level symptoms clearly pointing to it.

### 3. GitOps was not the only effective control path

The emergency recovery required applying the tracked CSIDriver manifest
manually. That restored service, but created temporary live/Git drift. A
successful emergency apply is not a substitute for making the owning Argo
application reconcile and prove ownership afterward.

### 4. Existing mounts masked the failure

The old proxy pod on `capstan1` retained an already-established mount. New
pods on `chronometer` and `capstan2` needed CSI operations and failed. This
made the failure appear intermittent and incorrectly suggested that the PVC
itself had been corrupted.

## Recovery performed

1. Restarted the `juicefs-csi-node` DaemonSet to recreate CSI sockets and node
   registration.
2. Confirmed `CSINode` registration on the affected nodes.
3. Re-applied the repository's `CSIDriver` manifest with
   `attachRequired: false`.
4. Removed unattached stale JuiceFS `VolumeAttachment` objects. No PVC or PV
   was deleted.
5. Confirmed the existing AI proxy PVC mounted and the original proxy became
   `2/2` ready.

## Correct operating model

### Resource ownership

- `CSIDriver/csi.juicefs.com` must have exactly one GitOps owner.
- `juicefs-sc` and any cache-specific StorageClass must have explicit owners
  and separate names.
- Do not rely on a Helm chart and a Kustomize application to co-own the same
  cluster-scoped object.
- The owning Argo application must include a health/sync check for the
  CSIDriver object, not only the CSI pods.

### Normal change workflow

1. Make the StorageClass, PVC, mount policy, and migration changes in Git.
2. Generate and inspect manifests before applying them.
3. Use a separate PR for migration infrastructure and workload cutover.
4. Sync the owning Argo applications in dependency order.
5. Verify before starting any copy:
   - `CSIDriver/csi.juicefs.com` exists.
   - `spec.attachRequired` is `false`.
   - every node has a `CSINode` entry for `csi.juicefs.com`.
   - all CSI node and controller pods are ready with no restart storm.
   - test PVCs mount on each intended node.
   - no unexpected unattached JuiceFS `VolumeAttachment` objects exist.
6. Run a small fixture migration and verify file counts, sizes, and reads.
7. Only then run the large migration and switch consumers.
8. After sync, verify the live objects against Git and remove any emergency
   manual edits.

### StorageClass rules

- Treat an existing StorageClass and PV as immutable infrastructure.
- Do not change `juicefs-sc` in place to perform a migration.
- Create a separately named StorageClass for a new JuiceFS metadata/backend
  domain, as `juicefs-cache-sc` attempted to do.
- A new StorageClass is not enough: its credentials, metadata database,
  formatting Job, mount policy, and rollback plan must be validated together.
- Never run a migration Job that requires a node with insufficient capacity;
  preflight scheduler placement and resource requests first.

### Emergency recovery rules

If CSI registration is lost:

1. Confirm `CSIDriver/csi.juicefs.com` exists and has
   `attachRequired: false`.
2. If it is missing, restore it from Git immediately and then repair GitOps
   ownership.
3. Restart the CSI node DaemonSet only after confirming the desired CSI image
   and mount policy.
4. Inspect stale `VolumeAttachment` objects. Delete only unattached stale
   objects after confirming `attachRequired: false`; never delete an attached
   object or a PVC/PV as a registration workaround.
5. Re-test one affected pod before restarting an entire workload.

## Follow-up actions

- [ ] Make one Argo application the sole owner of
      `CSIDriver/csi.juicefs.com`.
- [ ] Confirm the `juicefs-platform` application actually syncs
      `bootstrap/base/juicefs-platform/csidriver.yaml`.
- [ ] Add an Argo health or policy check for the CSIDriver object and
      `attachRequired: false`.
- [ ] Remove or explicitly stage the pending migration Job until its CPU,
      node-affinity, and rollback plan are approved.
- [ ] Reconcile the manually restored CSIDriver object through GitOps.
- [ ] Decide whether the strict-sharding image is production-ready before
      changing the shared `mountPodPatch`.
- [ ] Add a preflight command/checklist for CSI registration, mount pods, and
      stale VolumeAttachments to the JuiceFS migration procedure.
- [ ] Investigate the separate expired ChatGPT token before declaring the AI
      proxy rollout fully healthy.

## Key lesson

A `Bound` PVC is only the control-plane binding. Availability also depends on
CSI driver metadata, node registration, mount pods, FUSE state, and backend
connectivity. Cluster-scoped CSI metadata must be treated as a first-class
GitOps dependency, and storage migrations must be isolated, staged, and
validated before changing shared mount policy.
