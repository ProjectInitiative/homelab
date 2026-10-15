# garage-operator staging (CRD-based bucket/key provisioning against existing garage)

**Status: STAGED, NOT DEPLOYED.** Nothing references this directory until
deliberately enabled. The apps.yaml catalog entry is dormant (not in
clusters/mc.yaml, selfHeal off).

## Why

Provision garage buckets/keys via kubectl/CRDs instead of manual `garage` CLI
inside pods. Operator: https://github.com/rajsinghtech/garage-operator (v0.8.2)
— its "management handle" topology manages an EXISTING garage cluster via the
Admin API with zero operator-owned workloads.

## Current garage facts (verified 2026-10-15)

- Image `dxflrs/amd64_garage:v2.1.0`, chart `garage-0.9.1` (git-chart pinned ref
  `12367d30`), 3-node StatefulSet, `replication_factor: 3`,
  host-local-path-sticky PVCs (50Gi meta / 1Ti data).
- Admin API binds `[::]:3903` inside pods; **no `admin_token` configured**;
  `garage` Service exposes only 3900/3902. `garage-metrics` svc already
  routes 3903 — the staged management handle points there.
- cert-manager present (operator webhook dependency OK).
- Existing `garagenodes.deuxfleurs.fr` CRD = garage's own k8s discovery CRD —
  unrelated to the operator's `garage.rajsingh.info` group; no conflict.

## Staged files

- `management-handle.yaml` — GarageCluster w/ connectTo only (no workloads);
  token secret from OpenBao (`garage-admin-token`, key `admin-token`)
- `bucket-and-key.yaml` — GarageBucket `media` + GarageKey `s3-uploader`
  (read/write, non-owner); rename here if the bucket should be named
  differently

## Enablement checklist

### 1. Admin token secret (OpenBao)
kv-v2 `garage/operator-admin`, key `admin-token` = `openssl rand -hex 32`.
The apps.yaml entry's `vaultSecrets` block materializes it as
`garage-admin-token` in ns `garage`.

### 2. Wire the token into garage
Garage v2.1 reads `admin_token` from config or `GARAGE_ADMIN_TOKEN` env. The
chart supports `.Values.environment` on the main container:

```yaml
garage:
  environment:
    - name: GARAGE_ADMIN_TOKEN
      valueFrom:
        secretKeyRef:
          name: garage-admin-token
          key: admin-token
```

### 3. Install the operator
- Chart: `oci://ghcr.io/rajsinghtech/charts/garage-operator` version `0.8.2`,
  namespace `garage-operator-system`, `--set 'watchNamespaces={garage}'`.
- GitOps path: render once and commit under
  `bootstrap/base/garage-operator/operator/` (kustomize), or extend the CMP
  for OCI charts. First path is least invasive.

### 4. Enable the catalog entry
Add to `clusters/mc.yaml` apps: `- name: garage-operator`. Argo syncs:
CRDs → operator → VaultStaticSecret token → management handle → bucket+key.

### 5. Verify
```
kubectl wait --for=condition=Ready garagecluster/existing-garage -n garage --timeout=10m
kubectl wait --for=condition=Ready garagebucket/media -n garage --timeout=5m
kubectl wait --for=condition=Ready garagekey/s3-uploader -n garage --timeout=5m
kubectl -n garage get secret s3-uploader -o jsonpath='{.data.access-key-id}' | base64 -d; echo
```

## Rollback / kill switch

- `helm uninstall garage-operator -n garage-operator-system` (CRDs retained;
  bucket/key CRs become inert data — garage itself untouched).
- Management handle deletion touches nothing (no owned workloads).
- GarageBucket deletionPolicy defaults to `Delete` — set `Retain` before any
  delete-with-data experiment.

## Open questions

- Whether to keep the operator permanently or run it just for this migration
  and remove after (keel OQ-0037).
