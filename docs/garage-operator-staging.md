# garage-operator staging plan (esu-sound-library upload + CRD bucket/key provisioning)

**Status: STAGED, NOT DEPLOYED.** Everything in this doc + the
`bootstrap/base/garage-operator/` directory is dormant until deliberately
enabled. No Argo app references it today except the disabled `garage-operator`
catalog entry (see apps.yaml).

## Why

- Provision garage buckets/keys via kubectl/CRDs (no manual `garage` CLI dance
  inside pods) for the ESU sound-library extraction upload and future apps.
- Operator: https://github.com/rajsinghtech/garage-operator (v0.8.2), MIT,
  actively maintained, supports "management handle" topology — manages an
  EXISTING garage cluster via its Admin API with zero operator-owned workloads.

## Current garage facts (verified 2026-10-15)

- Image `dxflrs/amd64_garage:v2.1.0`, chart `garage-0.9.1` (git-chart pinned ref
  `12367d30`), 3-node StatefulSet, `replication_factor: 3`, juicefs-sc not
  involved (host-local-path-sticky PVCs 50Gi meta / 1Ti data).
- Admin API binds `[::]:3903` inside pods; **no `admin_token` configured**;
  `garage` Service exposes only 3900/3902 (admin reachable via
  `garage-s3-nodeport` nodePort 30826 + `garage-metrics` svc 3903).
- cert-manager present (webhook dependency OK).
- Existing `garagenodes.deuxfleurs.fr` CRD = garage's own k8s discovery CRD —
  unrelated to the operator's `garage.rajsingh.info` group; no conflict.

## Enablement checklist (when ready to test)

### 1. Admin token secret (OpenBao)
Add kv-v2 `garage/operator-admin` with key `admin-token` = `openssl rand -hex 32`.
The staged apps.yaml entry's `vaultSecrets` block materializes it as
`garage-admin-token` in ns `garage` (destination key `admin-token`).

### 2. Wire the token into garage
Garage v2.1 reads `admin_token` from config or `GARAGE_ADMIN_TOKEN` env.
Preferred: extend the init-container sed in the chart is invasive; simplest is
chart `environment` values (chart supports `.Values.environment` env block on
the main container):

```yaml
# garage-values.yaml
garage:
  environment:
    - name: GARAGE_ADMIN_TOKEN
      valueFrom:
        secretKeyRef:
          name: garage-admin-token
          key: admin-token
```

Then also expose admin on the `garage` Service: the chart renders Service ports
from config; simplest GitOps-shaped option is a small kustomize Service patch
in `bootstrap/base/garage/` adding port 3903 (`name: admin`) — or point the
management handle at the existing `garage-metrics` service (already 3903):
`http://garage-metrics.garage.svc:3903`.

### 3. Install the operator
- Chart: `oci://ghcr.io/rajsinghtech/charts/garage-operator` version `0.8.2`,
  namespace `garage-operator-system`, `--set 'watchNamespaces={garage}'`
  (namespace-scoped RBAC; release ns always watched).
- For the app catalog: either render the chart once and commit under
  `bootstrap/base/garage-operator/operator/` (kustomize), or extend the CMP to
  support OCI charts. First path is least invasive.

### 4. Enable the catalog entry
Add to `clusters/mc.yaml` apps: `- name: garage-operator`. Argo syncs:
CRDs → operator → VaultStaticSecret token → management handle → bucket+key.

### 5. Verify
```
kubectl wait --for=condition=Ready garagecluster/existing-garage -n garage --timeout=10m
kubectl wait --for=condition=Ready garagebucket/esu-sound-library -n garage --timeout=5m
kubectl wait --for=condition=Ready garagekey/esu-uploader -n garage --timeout=5m
kubectl -n garage get secret esu-uploader -o jsonpath='{.data.access-key-id}' | base64 -d; echo
```

### 6. Upload the ESU extraction
Point any S3 client at the secret's endpoint/creds; bucket `esu-sound-library`.
Source data: `~/development/sound-library/out_shay_final/` and
`out_emd_final/` (post-alignment-fix), plus `esu-key-bench` outputs
`out-esux/`, `out-test_project/` if wanted.

## Rollback / kill switch
- Operator uninstall: `helm uninstall garage-operator -n garage-operator-system`
  (CRDs retained by chart default; GarageBucket/GarageKey CRs remain as inert
  data — garage itself untouched).
- Management handle deletion touches nothing (no owned workloads).
- GarageBucket deletionPolicy defaults to `Delete` — set `Retain` on
  `esu-sound-library` before any delete-with-data experiment.

## Open questions
- Does the operator's webhook need to see garage v2.1 (it targets v2.0+;
  generated-key grammar is fine; imported-key v2.3 grammar not used here).
- Whether to keep the operator permanently (useful for future apps) or run it
  just for this migration and uninstall after.
