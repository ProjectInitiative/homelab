# Architecture & Workflow Guide

This document is the single source of truth for how this repository works. It covers the architecture, the Pulumi-based manifest generation, the multi-layer patch system, and step-by-step instructions for adding new apps with secrets.

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Argo CD (Control Cluster)                    │
│                                                                 │
│  root.yaml ──► Pulumi CMP ──► Generates Application CRDs        │
│                     │                                           │
│                     ▼                                           │
│         apps.yaml + clusters/*.yaml                             │
│                     │                                           │
│                     ▼                                           │
│            Argo CD Applications                                 │
│            (one per app per cluster)                            │
│                     │                                           │
│                     ▼                                           │
│         ┌───────────────────┐  ┌───────────────────┐           │
│         │  mc (capstan)     │  │  cc (homelab)     │           │
│         │  172.16.1.50:6443 │  │  in-cluster        │           │
│         └───────────────────┘  └───────────────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

**Key design principle:** Pulumi is a *manifest generator*, not an infrastructure provisioner. It reads declarative YAML configs (`apps.yaml` + `clusters/*.yaml`) and produces Argo CD `Application` CRDs. Argo CD then syncs those Applications to target clusters. The `bootstrap/` directory contains Kustomize bases and templates that the generated Applications reference.

---

## 2. Repository Structure

```
.
├── apps.yaml                    # CATALOG: defines every available app
├── clusters/
│   ├── mc.yaml                  # Main cluster (capstan) deployment config
│   └── cc.yaml                  # Control cluster (homelab) deployment config
├── pulumi/
│   ├── __main__.py              # Pulumi generator engine
│   ├── utils.py                 # camelCase → snake_case transformer
│   ├── Pulumi.yaml
│   ├── crd-imports.json         # CRD URLs for crd2pulumi
│   ├── crds/                    # Auto-generated Pulumi CRD types
│   │   └── pulumi_crds/
│   │       ├── argoproj/v1alpha1/   # Argo CD CRDs (Application, AppProject)
│   │       └── secrets/v1beta1/     # VSO CRDs (VaultAuth, VaultStaticSecret, etc.)
│   └── cmp-image/image.nix      # Nix build for Pulumi CMP Docker image
├── bootstrap/
│   ├── base/
│   │   ├── common/
│   │   │   ├── vault-resources/     # Placeholder templates for vault secrets
│   │   │   │   ├── auth/            # VaultAuth + ServiceAccount templates
│   │   │   │   └── secret/          # VaultStaticSecret template
│   │   │   └── pdb/                 # PodDisruptionBudget template for critical apps
│   │   ├── openbao-auth-config/     # VaultConnection + global VaultAuth
│   │   ├── openbao-secrets-operator/
│   │   ├── openbao/                 # OpenBao server (HA, TPM unseal)
│   │   ├── garage/                  # Garage S3 (uses kustomized-git-helm CMP)
│   │   ├── cnpg/database/           # Postgres cluster
│   │   ├── juicefs-platform/        # JuiceFS storage
│   │   ├── karmada-instance/        # Karmada control plane
│   │   ├── ...                      # Other bootstrap apps
│   └── mc/
│       ├── kube-vip/                # MC-specific kube-vip
│       └── garage-mem/              # MC-specific garage memory
├── apps/
│   └── base/                       # Cluster-agnostic application configs
│       ├── dnsutils/
│       ├── docker-registry/
│       ├── tailscale-proxy-groups/
│       └── temp-egress/
├── parent-apps/
│   ├── root.yaml                    # Root Argo CD Application (Pulumi source)
│   └── argocd-deployment-app.yaml   # Manages Argo CD CMP plugins
├── argocd-deployment/               # CMP plugin configs (ConfigMaps)
└── overlays/                        # LEGACY - old Kustomize approach (see §7)
```

---

## 3. The Pulumi Generation Engine

`pulumi/__main__.py` reads two inputs and produces Argo CD `Application` CRDs:

### Input: `apps.yaml` (The Catalog)

Defines every available application with its sources (Helm, Git, local path), vault secrets, sync policy, and other metadata:

```yaml
catalog:
  my-app:
    sources:
      - repoURL: https://charts.example.com
        chart: my-chart
        targetRevision: 1.0.0
        helm:
          values: |
            key: value
    vaultSecrets:
      createAuth: true           # Auto-generate VaultAuth + ServiceAccount
      role: openbao-secrets-operator
      namespace: production
      audiences: [vault]
      secrets:
        - name: my-secret
          mount: k8s
          path: "my-app/secret"
          destination: "my-k8s-secret"
    syncPolicy:
      syncOptions:
        - CreateNamespace=true
        - ServerSideApply=true
```

### Input: `clusters/<cluster>.yaml` (Deployment Config)

Defines which apps deploy to which cluster, overrides, and patches:

```yaml
name: mc
server: https://172.16.1.50:6443
project: mc-bootstrap
argoNamespace: argocd-mc
vaultMount: kubernetes_cluster_mc      # Per-cluster Vault auth mount path
apps:
  - name: my-app
    namespace: my-namespace
    helm_values: |
      replicaCount: 5
    patches:
      - patch: |
          - op: add
            path: /metadata/labels/foo
            value: bar
        target:
          kind: Deployment
          name: my-app
```

### Output: Argo CD `Application` CRDs

The Pulumi engine:
1. For each (app, cluster) pair, constructs an `Application` CR
2. Applies Helm values overrides from the cluster config
3. Applies Kustomize patches for the `patch`/`patches` fields
4. **Auto-generates VaultAuth + VaultStaticSecret sources** for apps with `vaultSecrets`
5. **Auto-generates PDB sources** for `critical: true` apps
6. Renders all Application CRDs as YAML to the manifests directory

---

## 4. The Multi-Layer Patch System

This is the most important concept to understand. The system uses **several layers of patching** to achieve modularity without code duplication:

### Layer 1: Pulumi-Generated Kustomize Patches (in Application CR)

The Pulumi engine reads `vaultSecrets` from `apps.yaml` and generates Kustomize patches that are embedded **inside the Argo CD Application spec**:

```yaml
# Generated Application CR (simplified)
apiVersion: argoproj.io/v1alpha1
kind: Application
spec:
  sources:
    # --- vault/auth source with patches ---
    - repoURL: https://github.com/projectinitiative/homelab.git
      targetRevision: HEAD
      path: bootstrap/base/common/vault-resources/auth
      kustomize:
        patches:
          # YAML Patch: replace VaultAuth spec (mount, role, SA)
          - patch: |
              apiVersion: secrets.hashicorp.com/v1beta1
              kind: VaultAuth
              metadata:
                name: placeholder-auth
                namespace: my-namespace
              spec:
                method: kubernetes
                mount: kubernetes_cluster_mc
                kubernetes:
                  role: openbao-secrets-operator
                  serviceAccount: operator-auth-sa
            target:
              kind: VaultAuth
              name: placeholder-auth
          # JSON Patch: rename placeholder-auth → my-app-auth
          - patch: |
              - op: replace
                path: /metadata/name
                value: my-app-auth
            target:
              kind: VaultAuth
              name: placeholder-auth
          # JSON Patch: rename placeholder-sa → operator-auth-sa
          - patch: |
              - op: replace
                path: /metadata/name
                value: operator-auth-sa
            target:
              kind: ServiceAccount
              name: placeholder-sa

    # --- vault/secret source with patches ---
    - repoURL: https://github.com/projectinitiative/homelab.git
      targetRevision: HEAD
      path: bootstrap/base/common/vault-resources/secret
      kustomize:
        patches:
          # YAML Patch: replace VaultStaticSecret spec
          - patch: |
              apiVersion: secrets.hashicorp.com/v1beta1
              kind: VaultStaticSecret
              ...
            target:
              kind: VaultStaticSecret
              name: placeholder-secret
          # JSON Patch: rename
          - patch: |
              - op: replace
                path: /metadata/name
                value: my-secret
            target:
              kind: VaultStaticSecret
              name: placeholder-secret

    # --- main app source ---
    - repoURL: https://charts.example.com
      chart: my-chart
      ...
```

The key insight: **Pulumi generates Kustomize patches at code-generation time**, which are then applied by Argo CD's CMP at sync time against the placeholder template files in `bootstrap/base/common/vault-resources/`.

### Layer 2: Kustomize in the CMP (at sync time)

When Argo CD syncs an Application with a Kustomize source, the CMP processes it:

1. Reads the template files (e.g., `vault-auth.yaml` with `placeholder-auth`)
2. Applies all Kustomize patches defined in `spec.source.kustomize.patches`
3. Produces finalized resources

### Layer 3: Cluster-Level App Patches (in `clusters/*.yaml`)

For legacy-style apps (the `patch` field in cluster configs), patches target resources *within* the app's own source:

```yaml
# clusters/mc.yaml
- name: openbao-auth-config
  namespace: kube-system
  patch: |-                        # This becomes a Kustomize patch
    apiVersion: secrets.hashicorp.com/v1beta1
    kind: VaultAuth
    metadata:
      name: operator-auth
    spec:
      mount: kubernetes_cluster_mc
      kubernetes:
        role: openbao-secrets-operator
  patchTarget:
    kind: VaultAuth
    name: operator-auth
```

### Layer 4: CMP Plugin Env Vars (for custom-kustomized apps)

Apps using custom CMPs (like `kustomized-git-helm`) pass configuration through `plugin.env`:

```yaml
# clusters/mc.yaml
- name: garage
  namespace: garage
  plugin:
    name: kustomized-git-helm-v1.0
    env:
      - name: HELM_VALUES
        value: |
          persistence:
            meta:
              storageClass: "host-local-path-nvme-sticky"
      - name: KUSTOMIZE_PATCH
        value: |
          - op: add
            path: /spec/volumeClaimTemplates/-
            value:
              metadata:
                name: snapshots
              ...
```

### Summary: The Full Patch Chain

```
apps.yaml (catalog)  ──►  clusters/*.yaml (deploy)
        │                          │
        ▼                          ▼
  ┌─────────────────────────────────────┐
  │  Pulumi Generator (__main__.py)     │
  │  • Reads catalog + deployment       │
  │  • Generates Application CRD        │
  │  • Creates Kustomize patches for    │
  │    vault resources, PDBs, etc.      │
  └──────────────┬──────────────────────┘
                 ▼
  ┌─────────────────────────────────────┐
  │  Argo CD Application CR             │
  │  • sources[].kustomize.patches      │
  │  • sources[].helm.values            │
  │  • sources[].plugin.env             │
  └──────────────┬──────────────────────┘
                 ▼
  ┌─────────────────────────────────────┐
  │  Argo CD CMP (at sync time)         │
  │  • Helm template → all.yaml         │
  │  • Kustomize build → apply patches  │
  │  • Rename, add labels, transform    │
  └──────────────┬──────────────────────┘
                 ▼
  ┌─────────────────────────────────────┐
  │  Target Cluster (mc or cc)          │
  │  • VaultAuth, VaultStaticSecret     │
  │  • Helm deployments, ConfigMaps     │
  │  • PodDisruptionBudgets, etc.       │
  └─────────────────────────────────────┘
```

---

## 5. Adding a New App (Without Secrets)

### Step 1: Define the app in `apps.yaml`

```yaml
catalog:
  my-new-app:
    sources:
      - repoURL: https://charts.bitnami.com/bitnami
        chart: nginx
        targetRevision: 15.0.0
        helm:
          values: |
            service:
              type: ClusterIP
    syncPolicy:
      syncOptions:
        - CreateNamespace=true
        - ServerSideApply=true
```

For a local-path app (Kustomize base in `bootstrap/` or `apps/`):

```yaml
catalog:
  my-new-app:
    path: apps/base/my-new-app/config
    syncPolicy:
      syncOptions:
        - ServerSideApply=true
```

### Step 2: Enable in `clusters/<cluster>.yaml`

```yaml
apps:
  - name: my-new-app
    namespace: my-namespace
    # Optional overrides
    helm_values: |
      replicaCount: 3
```

### Step 3: Generate and verify

```bash
nix run .#generate-manifests
nix run .#diff-manifests
```

---

## 6. Adding Secrets via OpenBao (VaultSecrets Abstraction)

### How Vault Secrets Flow

```
OpenBao (Vault)
    │
    │  (Vault Secrets Operator syncs)
    ▼
VaultStaticSecret CRD  ──►  Kubernetes Secret
    │
    │  (app consumes)
    ▼
Application Pod
```

### The CRDs

| CRD | API Version | Purpose |
|-----|-------------|---------|
| `VaultConnection` | `secrets.hashicorp.com/v1beta1` | Points VSO to the OpenBao server address |
| `VaultAuth` | `secrets.hashicorp.com/v1beta1` | Authentication method (Kubernetes) + role |
| `VaultStaticSecret` | `secrets.hashicorp.com/v1beta1` | Syncs a specific secret path to a K8s Secret |
| `VaultDynamicSecret` | `secrets.hashicorp.com/v1beta1` | Syncs dynamic/rotating secrets |
| `VaultPKISecret` | `secrets.hashicorp.com/v1beta1` | Syncs PKI certificates |

### Global Setup (Already in Place)

**VaultConnection** (`bootstrap/base/openbao-auth-config/config/vault-connection.yaml`):

```yaml
apiVersion: secrets.hashicorp.com/v1beta1
kind: VaultConnection
metadata:
  name: default
  namespace: openbao-secrets-operator
spec:
  address: http://100.122.64.114
  skipTLSVerify: true
```

**Global VaultAuth** per cluster (patched in `clusters/*.yaml`):

```yaml
# As defined in bootstrap/base/openbao-auth-config/config/operator-auth.yaml:
apiVersion: secrets.hashicorp.com/v1beta1
kind: VaultAuth
metadata:
  name: operator-auth
  namespace: openbao-secrets-operator
spec:
  method: kubernetes
  vaultConnectionRef: default
  mount: placeholder-mount-path    # Patched per cluster
  kubernetes:
    role: placeholder-role          # Patched per cluster
    serviceAccount: operator
```

The per-cluster patch sets the correct mount and role:

```yaml
# clusters/mc.yaml (for openbao-auth-config app)
patch: |-
  apiVersion: secrets.hashicorp.com/v1beta1
  kind: VaultAuth
  metadata:
    name: operator-auth
  spec:
    mount: kubernetes_cluster_mc
    kubernetes:
      role: openbao-secrets-operator
```

### Per-App Vault Secrets (Using `vaultSecrets`)

For apps that need their own secrets, use the `vaultSecrets` block in `apps.yaml`:

```yaml
catalog:
  my-app-with-secrets:
    sources:
      - repoURL: https://charts.example.com
        chart: my-chart
        targetRevision: 1.0.0

    vaultSecrets:
      # REQUIRED: Auto-generate dedicated VaultAuth and ServiceAccount
      createAuth: true
      # Auth name (defaults to "operator-auth" if omitted)
      auth: my-app-auth
      # Vault role to use
      role: openbao-secrets-operator
      # Vault namespace (if using Vault namespaces)
      namespace: production
      # Kubernetes audience for token review
      audiences:
        - vault

      secrets:
        # Each entry creates one VaultStaticSecret
        - name: my-creds                  # Name of the VaultStaticSecret resource
          mount: k8s                      # Vault secret mount point
          path: "my-app/credentials"      # Path in Vault
          destination: "my-app-creds"     # Name of the resulting K8s Secret
          # Optional: auth override (defaults to the auth field above)
          # auth: my-app-auth
          # Optional: refresh interval
          # refreshInterval: 60s
```

### What Pulumi Generates (Auto-Magic)

When `vaultSecrets.createAuth: true`, the Pulumi engine automatically:

1. **Creates a dedicated ServiceAccount** (named `{auth_name}-sa`, e.g., `operator-auth-sa`)
2. **Creates a dedicated VaultAuth** that uses Kubernetes auth with that SA
3. **Creates VaultStaticSecret resources** for each entry in `secrets` list
4. **Labels the namespace** with `vault-auth: enabled`

All of this is done by generating Kustomize patches against the placeholder templates in `bootstrap/base/common/vault-resources/`.

### On the Vault Server Side

After deploying, you must configure OpenBao with:

1. A Kubernetes auth mount at the cluster's mount path (e.g., `kubernetes_cluster_mc`)
2. A role that binds the generated ServiceAccount name and namespace to the appropriate Vault policy
3. The actual secrets at the specified paths

### Step-by-Step: Adding Secrets to an Existing App

1. Add the `vaultSecrets` block to the app's catalog entry in `apps.yaml`
2. Enable the app in the cluster config (if not already)
3. Run `nix run .#generate-manifests` to verify
4. On the Vault server, create the role and secret at the specified path

### Real Examples from This Repo

**Tailscale Operator** (simplest example):

```yaml
tailscale-operator:
  sources:
    - repoURL: https://pkgs.tailscale.com/helmcharts
      chart: tailscale-operator
      targetRevision: 1.92.4
  vaultSecrets:
    createAuth: true
    role: openbao-secrets-operator
    namespace: production
    audiences:
      - vault
    secrets:
      - name: tailscale-auth
        mount: k8s
        path: "tailscale-operator"
        destination: "operator-oauth"
```

This creates:
- `VaultAuth` named `operator-auth` in the `tailscale` namespace (using Kubernetes auth)
- `ServiceAccount` named `operator-auth-sa` in the `tailscale` namespace
- `VaultStaticSecret` named `tailscale-auth` that syncs `tailscale-operator` path to K8s Secret `operator-oauth`

**Postgres Cluster** (secret from `cnpg/s3` path):

```yaml
postgres-cluster:
  path: bootstrap/base/cnpg/database
  vaultSecrets:
    createAuth: true
    role: openbao-secrets-operator
    namespace: production
    audiences:
      - vault
    secrets:
      - name: postgres-cluster-s3
        mount: k8s
        path: "cnpg/s3"
        destination: "postgres-cluster-s3"
```

---

## 7. Legacy Overlays (Reference Only)

The `overlays/` directory contains the **old** Kustomize-based approach that this system replaced. It is kept for reference but should NOT be modified.

The old system:
- Used `overlays/main-cluster/kustomization.yaml` and `overlays/control-cluster/kustomization.yaml`
- Each overlay referenced bootstrap bases and applied JSON patches
- Used **meta-patching**: patches on Argo CD Application CRs that injected more patches into their Kustomize config
- Was complex, hard to follow, and required duplicating cluster-specific logic in multiple places

The Pulumi approach replaced this by centralizing all generation logic in `pulumi/__main__.py`, making the system declarative and much easier to understand.

---

## 8. Development Workflow

### Setup

```bash
# Enter the Nix development environment
nix develop
# or if using direnv:
direnv allow
```

### Generate Local Preview

```bash
nix run .#generate-manifests
```

This runs the Pulumi generator and outputs manifest YAML to `.direnv/manifests/`.

### Diff Against Main

```bash
nix run .#diff-manifests
```

This compares the generated manifests against the `main` branch state.

### Import/Update CRDs (Rarely Needed)

```bash
nix run .#import-crds pulumi/crd-imports.json
```

This regenerates the Pulumi CRD type stubs in `pulumi/crds/` using `crd2pulumi`.

### Commit and Deploy

1. Edit `apps.yaml` and/or `clusters/*.yaml` (never `manifests/` directly)
2. Run `nix run .#generate-manifests` to preview
3. Run `nix run .#diff-manifests` to check for unexpected changes
4. Commit both config files (manifests are optional for record-keeping)
5. Argo CD automatically picks up the changes and re-syncs

### Debugging

- **Generation fails**: Check YAML syntax in `apps.yaml` and `clusters/*.yaml`
- **Unexpected diff**: The Pulumi generator may have a bug or a shared config changed
- **Vault secrets not syncing**: Verify the VaultAuth is correct, the ServiceAccount exists, and Vault has the role configured
- **CRD imports failing**: Check `pulumi/crd-imports.json` URLs are reachable

---

## 9. Key Abstractions & Fields Reference

### `vaultSecrets` (in `apps.yaml`)

| Field | Default | Description |
|-------|---------|-------------|
| `createAuth` | `false` | Auto-generate VaultAuth + ServiceAccount |
| `auth` | `"operator-auth"` | Name for the VaultAuth resource |
| `role` | `"openbao-secrets-operator"` | Vault role to use in auth |
| `namespace` | (none) | Vault namespace (OpenBao Enterprise feature) |
| `audiences` | `[]` | Kubernetes token review audiences |
| `secrets` | `[]` | List of VaultStaticSecret definitions |

### `secrets[]` items

| Field | Required | Description |
|-------|----------|-------------|
| `name` | yes | Resource name for the VaultStaticSecret |
| `mount` | no | Vault secrets engine mount (default: `"secret"`) |
| `path` | yes | Path in Vault to the secret |
| `destination` | yes | Name of the resulting Kubernetes Secret |
| `type` | no | Secret type (default: `"kv-v2"`) |
| `auth` | no | Override auth name for this secret |
| `refreshInterval` | no | How often to refresh from Vault |

### `critical: true` (in `apps.yaml`)

- Injects a `PodDisruptionBudget` (maxUnavailable: 1) with label `policy.homelab.io/protected: "true"`
- Injects the `ADD_PROTECTED_LABEL` env var, which adds `policy.homelab.io/protected: "true"` as a Kustomize commonLabel

### `patches` (in `clusters/*.yaml`)

| Field | Type | Description |
|-------|------|-------------|
| `patch` | string | JSON Patch (RFC 6902) or strategic merge patch |
| `target` | object | (optional) `{kind, name, group, version}` to target specific resources |
| `sourceIndex` | integer | (optional) Which source in the sources list to patch (default: 0) |
