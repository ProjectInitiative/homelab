# Garage Operator Migration Report

## 1. The Two Repos

### garage-operator (`vendor/garage-operator/`)

| Aspect | Assessment |
|--------|------------|
| Maturity | High — kubebuilder-based, v2 Admin API, E2E tests, Helm chart, multi-arch, webhooks, active development |
| What it manages | Full cluster lifecycle: StatefulSet, PVCs, ConfigMap (garage.toml), Services, layout, federation, PDB, monitoring |
| Data-plane CRDs | GarageBucket, GarageKey, GarageNode, GarageAdminToken, GarageReferenceGrant |
| Admin API version | **v2** (modern) |

### garage-crossplane-provider (`vendor/garage-crossplane-provider/`)

| Aspect | Assessment |
|--------|------------|
| Maturity | Early — limited testing, basic feature set |
| What it manages | Buckets, keys, permissions only (assumes existing cluster) |
| Admin API version | **v1** (deprecated — code uses `/v1/` endpoints despite README claiming v2) |
| Requirement | Requires Crossplane platform installed |

## 2. Why the Operator Won't Work Alongside Helm

The operator's bucket/key controllers are **tightly coupled** to the `GarageCluster` CR:

- `GarageBucket.Spec.ClusterRef` is **required** — you cannot create a bucket without referencing a cluster
- The admin API endpoint is **hardcoded** to `http://<cluster.Name>.<namespace>.svc.<clusterDomain>:3903` — you cannot override it
- The cluster controller **unconditionally** creates a StatefulSet, Service, and ConfigMap
- No "external cluster" / BYO mode exists anywhere in the codebase
- The `BucketID` field allows pinning to a pre-existing bucket, but the cluster controller still needs a running Garage pod to talk to

**Result**: Running the operator against a Helm-managed Garage would create a *second* Garage StatefulSet that collides with the existing one.

## 3. Migration Path (Operator-Managed)

If you want to migrate from Helm to the operator:

### Phase 1: Parallel Test Cluster

Deploy the operator + a test `GarageCluster` alongside the existing Helm deployment to learn its behavior:

```
Current:  Helm → garage.mc.svc:3900 (S3)
Test:     Operator → test-cluster.test.svc:3900 (S3)
```

Create `GarageBucket` resources against the test cluster. Validate that `GarageBucket.Spec.BucketID` can adopt existing buckets post-migration.

### Phase 2: Data Backup

Use Garage's Admin API to backup all bucket data and metadata:

```bash
# Dump cluster state (buckets, keys, permissions, layout)
garage admin cluster info

# For each bucket, use s3 tools to copy data out
aws s3 sync s3://my-bucket ./backups/my-bucket/ --endpoint-url http://garage.garage.svc.cluster.local:3900
```

Total data to check: garage has `persistence.data.size: 1024Gi` and `persistence.meta.size: 50Gi`.

### Phase 3: Helm → Operator Cutover

1. Back up existing Garage PVCs (snapshot or rsync data out)
2. Delete the Helm-managed Garage (keep PVCs: `--cascade=orphan`)
3. Deploy operator and create `GarageCluster` CR matching the existing storage layout:
   - 3 replicas, same StorageClass (`local-path-nvme-sticky`), same PVC sizes
   - `spec.storage.data.storage.size: 1024Gi`
   - `spec.storage.metadata.storage.size: 50Gi`
4. The operator will find the existing PVCs and adopt them (StatefulSet controller behavior, not operator-specific — same headless service name → same PVCs)
5. Restore any data if needed

### Phase 4: Verify and Profit

1. Confirm Garage pods come up with existing data
2. Create `GarageBucket` + `GarageKey` CRs for apps that need buckets
3. Remove any Helm leftovers (ConfigMaps, Secrets the operator now manages)

## 4. Risks

| Risk | Mitigation |
|------|------------|
| Operator's generated `garage.toml` differs from Helm's config | Thoroughly map current Helm values to operator CR spec fields before cutover. The 3-node layout, storage classes, and network config must match. |
| Rolling restart during cutover | 3-replica cluster should survive with no downtime if done carefully. Garage handles topology changes. |
| StatefulSet adoption edge case | StatefulSet adoption by a new owner can be clean if the name matches and PVCs are retained. Test in parallel first. |
| Operator bug | Keep backups. The operator is actively developed but not battle-tested in your environment. |

## 5. Recommendation

**The operator migration is viable** and would give you:
- Declarative `GarageBucket` + `GarageKey` CRDs for apps
- Self-healing cluster management (layout, repairs, scrubs)
- Monitoring + PDB built in
- COSI driver option

**But test it in parallel first.** Drop the operator + a test cluster into the `garage` namespace alongside the Helm deployment to validate bucket/key CRD functionality before touching the real data.

The alternative — a custom lightweight controller with just `Bucket`/`BucketAccess` CRDs that talks v2 Admin API directly — would be cleaner architecturally but requires building and maintaining it.
