# Garage Operator Migration — Test/Conversion

This directory contains the conversion of the current Helm-based Garage deployment
to the garage-operator's `GarageCluster` CR format. It is NOT deployed — it's a
reference for the migration.

## Current Helm Config (source)

- **Chart**: `script/helm/garage` at commit `12367d307b365f947936cf18b90b0f5b7607da5d` from `https://git.deuxfleurs.fr/Deuxfleurs/garage`
- **Values**: `bootstrap/base/garage/garage-values.yaml` + overrides in `clusters/mc.yaml`
- **S3 endpoint**: `garage.garage.svc.cluster.local:3900`
- **RPC secret**: from Vault, synced to K8s secret `garage-rpc-secret`
- **Admin API**: port 3903, file-based admin token (auto-managed by Helm chart)

## Vault Secrets

Both critical secrets are pre-provisioned in OpenBao and synced via VSO, so the
operator references existing K8s secrets rather than auto-generating them:

| Vault Path | K8s Secret | Purpose |
|------------|-----------|---------|
| `k8s/garage/rpc` | `garage-rpc-secret` | RPC secret (already exists) |
| `k8s/garage/admin-token` | `garage-admin-token` | Admin API token (needs creation on Vault side) |

Both are referenced in `garage-cluster.yaml` via `rpcSecretRef` and
`adminTokenSecretRef`. The operator will NOT regenerate them.

## Key Mapping

| Helm Value | Operator CR Field |
|------------|------------------|
| `deployment.replicaCount: 3` | `spec.storage.replicas: 3` |
| `garage.replicationFactor: 3` | `spec.replication.factor: 3` |
| `garage.consistencyMode: "consistent"` | `spec.replication.consistencyMode: consistent` |
| `garage.dbEngine: "lmdb"` | `spec.database.engine: lmdb` |
| `garage.blockSize: "10M"` | `spec.blocks.size: 10Mi` (converted) |
| `persistence.meta.size: 50Gi` | `spec.storage.metadata.size: 50Gi` |
| `persistence.data.size: 1024Gi` | `spec.storage.data.size: 1024Gi` |
| `persistence.meta.storageClass: "host-local-path-nvme-sticky"` | `spec.storage.metadata.storageClass` (via `storageClassName`) |
| `garage.rpcBindAddr: "[::]:3901"` | `spec.network.rpcBindPort: 3901` |
| `garage.s3.api.region: "us-east-1"` | `spec.s3Api.region: us-east-1` |
| `garage.s3.api.rootDomain: ".s3.moonwake.io"` | Not in operator (LB/ingress config) |
| `garage.monitoring.metrics.enabled: true` | `spec.monitoring.metrics.enabled: true` |
| `garage.rpcBindAddr: "[::]:3901"` | `spec.network.rpcBindPort: 3901` |
| Extra Volume: snapshots (20Gi, HDD) | `spec.storage.extraVolumes` (see garage-cluster.yaml) |

## Migration Steps (When Ready)

1. Deploy operator into `garage-operator-system` namespace
2. Create the admin token secret (`admin-token-secret.yaml`)
3. Create the `GarageCluster` CR (this will deploy a SECOND Garage alongside the Helm one)
4. Validate GarageBucket/GarageKey CRD functionality
5. When ready for cutover: backup data, delete Helm release with `--cascade=orphan`, operator adopts PVCs
