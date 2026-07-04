# Migration Plan: Pulumi → cdk8s

## Background

### Root Cause
The devenv migration (commit `c26b39d`) bumped nixpkgs from `c6245e83d836` → `a799d3e3886d`,
which updated `pulumi-kubernetes` from v3 → **v4.25.0**. In v4, the provider was rewritten
from Python to Go, and `render_yaml_to_directory` was **removed** — it's silently accepted
but has no effect. As a result, `pulumi up` completes successfully ("46 unchanged") but writes
zero YAML files to disk. This broke both local manifest generation and the CMP image.

### Why cdk8s
- **Purpose-built** for generating Kubernetes manifests as YAML files (no cluster connection, no state)
- **Construct composition**: cdk8s is built on the `constructs` library, designed for sharing and
  composing resource definitions across projects. You can publish cdk8s constructs as a Python
  package (pip) and import them in any other cdk8s project — this is a core feature.
- **CRD type generation**: `cdk8s import` generates typed Python classes from CRD YAML files
  (replaces `crd2pulumi`).
- **Future foundation**: cdk8s+ provides high-level abstractions (Deployment, Service, Ingress, etc.)
  with type safety, which can be used to define actual application deployments in the future.

### Tradeoff: jsii and Node.js

cdk8s Python uses **jsii** (AWS's Python↔JavaScript bridge). The architecture:
- `cdk8s`, `constructs`, and `jsii` are pure-Python wheels on PyPI — they bundle a
  **minified JS bundle inside the wheel** (no separate `node_modules` at build/install time)
- At **runtime**, the `jsii._kernel` module spawns a **Node.js subprocess** to execute the
  bundled JS bundle. So `node` must be on `PATH` when `app.synth()` runs
- `cdk8s synth` just runs `python main.py` — the CLI itself is not needed at synth time

### How uv2nix + devenv handles this

This was previously impossible because the JSII packages were "fundamentally incompatible"
with Nix's hermeticity model — old approaches (`pip2nix`, `mach-nix`, manual `buildPythonPackage`)
tried to bundle Node.js inside the Python derivation, fighting Nix's sandbox.

uv2nix sidesteps this entirely by treating jsii/cdk8s/constructs as **ordinary Python wheels**
(which they are — the JS bundle is inside the wheel data, and uv2nix copies it verbatim).
The only accommodations needed:

1. **uv2nix** generates Nix derivations from `generator/uv.lock` for `cdk8s`, `constructs`,
   `jsii` and all transitive Python deps. These are pure-Python wheels — no patching needed.
2. **devenv** adds `nodejs` to `packages`. jsii finds `node` in `PATH` at runtime via standard
   `subprocess` lookup. No vendor bundling, no FHS, no patching of the wheel.
3. **CMP image**: `nodejs` is added to `contents` of the Docker image (one extra layer).
   jsii spawns `node` from `PATH` at synth time.

This is **slightly less hermetic** than a fully-vendored Nix build (Node.js version is pinned by
nixpkgs, not by the Python lockfile), but pragmatic and reproducible. The Python side is fully
locked via `uv.lock` + uv2nix; the Node.js side is just a runtime tool like `git` or `curl`.

### Fallback: cdk8s Go module

If the jsii + Node.js path proves too fragile in practice (e.g., CMP image bloat, ARM cross-comp
issues with Node.js), the entire generator can be rewritten using the **cdk8s Go SDK**:
- Native single-binary deployment (no Node.js, no Python, no subprocess)
- All cdk8s features available (Charts, ApiObjects, Construct composition, `cdk8s import`)
- Construct sharing works via Go modules
- nixpkgs has excellent Go tooling

This is documented as the fallback plan in Phase 8.

### `cdk8s-cli` in nixpkgs

The `cdk8s-cli` Node.js package IS available in nixpkgs at
`pkgs/by-name/cd/cdk8s-cli/package.nix` (v2.206.x). It's only needed for:
- `cdk8s import` — generates Python CRD classes (run rarely, output committed to repo)
- `cdk8s init` — scaffolds a new project (one-time only)

It is NOT needed at synth time — `cdk8s synth` just executes `python main.py`.

### What Stays vs What Changes

| Component | Before (Pulumi) | After (cdk8s) |
|-----------|-----------------|---------------|
| Manifest generator | `pulumi/__main__.py` (~447 lines) | `generator/main.py` (ported logic) |
| CRD type generation | `crd2pulumi` + `pulumi/crds/` | `cdk8s import` + `generator/imports/` |
| CRD import config | `pulumi/crd-imports.json` | `generator/cdk8s.yaml` |
| Helper utilities | `pulumi/utils.py` (`recursive_transform`) | **Deleted** (not needed — cdk8s accepts camelCase dicts) |
| State management | Pulumi local backend (`~/.pulumi/`) | **None** (Pure function: config → YAML) |
| Runtime deps | `pulumi`, `pulumi-kubernetes`, `pulumi_crds` | `cdk8s`, `constructs`, `jsii` (Python) + Node.js |
| CMP image | `pulumi/cmp-image/image.nix` | `generator/cmp-image/image.nix` |
| Nix scripts | `nix/scripts/generate-manifests.nix`, `setup-pulumi.nix`, `import-crds.nix` | Updated equivalents |

---

## Phase 1: Generate Baseline Snapshot (from current code)

Before migrating, capture the *correct* output of the current generator so we can validate
the cdk8s port produces identical manifests.

### 1.1 Patch `pulumi/__main__.py` to Write YAML Directly

The current code constructs `app_manifest` as a plain dict (lines 379-399), then passes it to
Pulumi's `Application()` constructor (lines 402-413). We bypass the broken Pulumi provider by
writing YAML directly.

**Edit `pulumi/__main__.py`:**

1. Remove these imports and the provider setup (lines 1-11, 31-35):
```python
# DELETE these lines:
import pulumi
import pulumi_kubernetes as k8s
from pulumi_crds.argoproj.v1alpha1 import Application
from utils import recursive_transform

render_dir = os.environ.get("PULUMI_MANIFEST_OUTPUT_DIR", os.path.join(os.getcwd(), "manifests"))
k8s_provider = k8s.Provider("k8s-yaml-renderer", 
    render_yaml_to_directory=render_dir
)
```

Keep `yaml`, `json`, `os`, `sys`, `copy` imports.

2. Replace the Pulumi resource creation (lines 401-413) with direct YAML writing:
```python
# DELETE these lines:
app_args = recursive_transform(app_manifest)
resource_name = f"{cluster_name}-{app_name}"
Application(
    resource_name,
    **app_args,
    opts=pulumi.ResourceOptions(provider=k8s_provider, protect=False) 
)

# REPLACE WITH:
out_dir = os.environ.get("MANIFEST_OUTPUT_DIR", 
    os.path.join(os.getcwd(), "..", "manifests"))
os.makedirs(out_dir, exist_ok=True)

file_path = os.path.join(out_dir, f"{cluster_name}-{app_name}.yaml")
with open(file_path, 'w') as f:
    yaml.safe_dump(app_manifest, f, default_flow_style=False, sort_keys=False)
```

3. Fix the stale cluster file list (line 443) — `clusters/karmada.yaml` does not exist:
```python
# BEFORE:
clusters_files = ['clusters/mc.yaml', 'clusters/cc.yaml', 'clusters/karmada.yaml']

# AFTER:
clusters_files = ['clusters/mc.yaml', 'clusters/cc.yaml']
```

### 1.2 Generate the Baseline

```bash
devenv shell
export MANIFEST_OUTPUT_DIR=$(pwd)/snapshot-baseline
cd pulumi
python __main__.py
```

This writes one YAML file per (cluster, app) pair to `snapshot-baseline/`.
Verify the output contains all expected apps (mc has ~25 apps, cc has ~16 apps):

```bash
ls snapshot-baseline/
# Expected: mc-kube-vip-app.yaml, mc-admin-access.yaml, ..., cc-local-path-provisioner.yaml, etc.
cat snapshot-baseline/mc-kubevirt.yaml  # Verify kubevirt is present
```

---

## Phase 2: Set Up the cdk8s Environment

### 2.1 Create the Generator Directory

```bash
mkdir -p generator
cd generator
```

### 2.2 Create `generator/cdk8s.yaml`

This replaces `pulumi/crd-imports.json`. It configures the cdk8s project and declares which
CRDs to import. The import URLs are the same as the current `crd-imports.json`.

```yaml
# generator/cdk8s.yaml
language: python
app: python main.py
imports:
  # Argo CD CRDs
  - https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/crds/application-crd.yaml
  - https://raw.githubusercontent.com/argoproj/argo-cd/refs/heads/master/manifests/crds/applicationset-crd.yaml
  - https://raw.githubusercontent.com/argoproj/argo-cd/refs/heads/master/manifests/crds/appproject-crd.yaml
  # VSO (Vault Secrets Operator) CRDs
  - https://raw.githubusercontent.com/hashicorp/vault-secrets-operator/v1.4.0/chart/crds/secrets.hashicorp.com_vaultauths.yaml
  - https://raw.githubusercontent.com/hashicorp/vault-secrets-operator/v1.4.0/chart/crds/secrets.hashicorp.com_vaultconnections.yaml
  - https://raw.githubusercontent.com/hashicorp/vault-secrets-operator/v1.4.0/chart/crds/secrets.hashicorp.com_vaultstaticsecrets.yaml
  - https://raw.githubusercontent.com/hashicorp/vault-secrets-operator/v1.4.0/chart/crds/secrets.hashicorp.com_vaultdynamicsecrets.yaml
  - https://raw.githubusercontent.com/hashicorp/vault-secrets-operator/v1.4.0/chart/crds/secrets.hashicorp.com_vaultpkisecrets.yaml
```

### 2.3 Create `generator/pyproject.toml`

Declares the Python dependencies for the generator. These are NOT in nixpkgs, so they're
installed via `uv` (which is already used in the devenv shell).

```toml
[project]
name = "homelab-generator"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "cdk8s>=2.0.0",
    "constructs>=10.0.0",
    "jsii>=1.0.0",
    "pyyaml>=6.0",
]

[tool.uv]
dev-dependencies = []
```

### 2.4 Import CRDs

This generates typed Python classes under `generator/imports/`. Requires the `cdk8s-cli`
Node.js package.

```bash
cd generator
cdk8s import
```

This creates:
```
generator/imports/
├── __init__.py
├── argoproj/
│   └── io/
│       ├── __init__.py
│       └── application.py    # Typed `Application` class
│       └── applicationset.py
│       └── appproject.py
└── secrets/
    └── hashicorp.com/
        ├── __init__.py
        └── vaultauth.py       # Typed `VaultAuth` class
        └── vaultconnection.py
        └── vaultstaticsecret.py
        └── vaultdynamicsecret.py
        └── vaultpkisecret.py
```

> **Note:** These generated files should be committed to the repo (per cdk8s documentation).
> They are deterministic and don't need to be regenerated unless CRD URLs change.

### 2.5 Verify the Environment

```bash
cd generator
python -c "from cdk8s import App, Chart, ApiObject; print('cdk8s OK')"
python -c "from imports.argoproj.io import Application; print('CRD imports OK')"
```

---

## Phase 3: Port the Generator Logic

### 3.1 Architecture of `generator/main.py`

The existing `pulumi/__main__.py` has ~447 lines. The core logic (lines 37-399) is
**framework-agnostic** — it reads YAML configs and builds `app_manifest` dicts. Only
the bottom ~15 lines are Pulumi-specific.

The port:
1. Keeps all config parsing, source building, patch application, vault secrets, and
   critical-app logic **exactly as-is**
2. Wraps the final `app_manifest` dict in `cdk8s.ApiObject` (no `recursive_transform`)
3. Uses one `Chart` per cluster (so output is organized by cluster)
4. Disables resource name hashing (we set explicit `metadata.name` on every resource)

### 3.2 Write `generator/main.py`

```python
#!/usr/bin/env python3
"""Homelab Argo CD Application manifest generator (cdk8s)."""

import yaml
import json
import os
import sys
import copy

from cdk8s import App, Chart, ApiObject
from constructs import Construct


def load_yaml(path):
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return yaml.safe_load(f)


# --- Config paths ---
# Resolve project root (generator/ is one level below root)
GENERATOR_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(GENERATOR_DIR)

apps_catalog = load_yaml(os.path.join(ROOT_DIR, "apps.yaml"))
if not apps_catalog:
    print(f"Error: apps.yaml not found", file=sys.stderr)
    sys.exit(1)

defaults = apps_catalog.get("defaults", {})
catalog = apps_catalog.get("catalog", {})


def apply_patch_to_source(src_obj, patch_content, patch_target=None):
    """Add a Kustomize patch to an Argo CD source's kustomize config."""
    if "kustomize" not in src_obj:
        src_obj["kustomize"] = {}
    patch_entry = {"patch": patch_content}
    if patch_target:
        patch_entry["target"] = patch_target
    if "patches" not in src_obj["kustomize"]:
        src_obj["kustomize"]["patches"] = []
    src_obj["kustomize"]["patches"].append(patch_entry)


class ClusterAppsChart(Chart):
    """One Chart per cluster. Produces all Application CRDs for that cluster."""

    def __init__(self, scope: Construct, cluster_file: str):
        cluster_config = load_yaml(cluster_file)
        if not cluster_config:
            return

        cluster_name = cluster_config["name"]
        server_url = cluster_config["server"]
        argo_namespace = cluster_config["argoNamespace"]
        vault_mount = cluster_config.get("vaultMount")

        # Disable hash suffixes — we set explicit metadata.name on every resource
        super().__init__(scope, cluster_name, disable_resource_name_hashes=True)

        print(f"Processing cluster: {cluster_name} ({server_url})", file=sys.stderr)

        apps = cluster_config.get("apps", [])
        for app_deployment in apps:
            app_name = app_deployment["name"]

            app_def = catalog.get(app_name)
            if not app_def:
                print(
                    f"  [WARN] App '{app_name}' not found in apps.yaml catalog. Skipping.",
                    file=sys.stderr,
                )
                continue

            target_ns = app_deployment.get("namespace")
            if not target_ns:
                print(
                    f"  [WARN] Namespace not specified for '{app_name}' in {cluster_name}. Skipping.",
                    file=sys.stderr,
                )
                continue

            print(f"  Generating '{app_name}' for '{target_ns}'", file=sys.stderr)

            app_manifest = self._build_app_manifest(
                app_name,
                app_def,
                app_deployment,
                cluster_config,
                server_url,
                argo_namespace,
                target_ns,
                vault_mount,
                cluster_name,
            )

            # Wrap the dict in an ApiObject — no key transformation needed
            # cdk8s preserves the exact field names we pass
            ApiObject(
                self,
                f"{cluster_name}-{app_name}",
                api_version=app_manifest["apiVersion"],
                kind=app_manifest["kind"],
                metadata=app_manifest["metadata"],
                spec=app_manifest["spec"],
            )

    def _build_app_manifest(
        self,
        app_name,
        app_def,
        app_deployment,
        cluster_config,
        server_url,
        argo_namespace,
        target_ns,
        vault_mount,
        cluster_name,
    ):
        """Construct the Application CR dict. This is the ported logic from __main__.py."""
        # === 1. Source(s) ===
        sources = []
        if "sources" in app_def:
            sources = copy.deepcopy(app_def["sources"])
        else:
            # Legacy single source construction
            source = {
                "repoURL": app_def.get("repoURL", defaults.get("repoURL")),
                "targetRevision": app_def.get(
                    "targetRevision", defaults.get("targetRevision")
                ),
                "path": app_def.get("path"),
                "chart": app_def.get("chart"),
            }
            if "directory" in app_def:
                source["directory"] = app_def["directory"]
            if "plugin" in app_deployment:
                source["plugin"] = app_deployment["plugin"]
            elif "plugin" in app_def:
                source["plugin"] = app_def["plugin"]
            source = {k: v for k, v in source.items() if v is not None}
            sources = [source]

        # === 2. Legacy single patch ===
        if "patch" in app_deployment and app_deployment["patch"]:
            legacy_target_source = None
            if "patchSourceIndex" in app_deployment:
                idx = app_deployment["patchSourceIndex"]
                if 0 <= idx < len(sources):
                    legacy_target_source = sources[idx]
            if legacy_target_source is None:
                for src in sources:
                    if "path" in src and (
                        src.get("path", "").endswith("config") or "kustomize" in src
                    ):
                        legacy_target_source = src
                        break
                if legacy_target_source is None:
                    legacy_target_source = sources[0]
            apply_patch_to_source(
                legacy_target_source,
                app_deployment["patch"],
                app_deployment.get("patchTarget"),
            )

        # === 3. Multi-patch support ===
        if "patches" in app_deployment and isinstance(app_deployment["patches"], list):
            for p in app_deployment["patches"]:
                if "patch" not in p:
                    continue
                patch_src_idx = p.get("sourceIndex", 0)
                if 0 <= patch_src_idx < len(sources):
                    apply_patch_to_source(
                        sources[patch_src_idx], p["patch"], p.get("target")
                    )

        # === 4. Helm values ===
        target_source_for_helm_values = None
        if "helmValuesSourceIndex" in app_deployment:
            idx = app_deployment["helmValuesSourceIndex"]
            if 0 <= idx < len(sources):
                target_source_for_helm_values = sources[idx]
        if target_source_for_helm_values is None:
            for src in sources:
                if "chart" in src and "helm" in src:
                    target_source_for_helm_values = src
        if target_source_for_helm_values is None:
            target_source_for_helm_values = sources[0]

        if "helm_values" in app_deployment or "value_files" in app_deployment:
            if "helm" not in target_source_for_helm_values:
                target_source_for_helm_values["helm"] = {}
            if "helm_values" in app_deployment:
                target_source_for_helm_values["helm"]["values"] = app_deployment[
                    "helm_values"
                ]
            if "value_files" in app_deployment:
                existing = target_source_for_helm_values["helm"].get("valueFiles", [])
                if not isinstance(existing, list):
                    existing = [existing]
                new_files = app_deployment["value_files"]
                if not isinstance(new_files, list):
                    new_files = [new_files]
                target_source_for_helm_values["helm"]["valueFiles"] = existing + new_files

        # === 5. Vault Secrets (auto-injection) ===
        if "vaultSecrets" in app_def:
            vs_config = app_def["vaultSecrets"]
            secrets_list = vs_config.get("secrets", [])
            default_auth_name = vs_config.get("auth", "operator-auth")
            common_repo = {
                "repoURL": "https://github.com/projectinitiative/homelab.git",
                "targetRevision": "HEAD",
            }

            # Auto-create VaultAuth
            if vs_config.get("createAuth", False):
                if not vault_mount:
                    print(
                        f"  [WARN] 'createAuth' is True for '{app_name}' but vaultMount not defined. Skipping.",
                        file=sys.stderr,
                    )
                else:
                    vault_role = vs_config.get("role", "openbao-secrets-operator")
                    generated_sa_name = f"{default_auth_name}-sa"
                    audiences = vs_config.get("audiences", [])

                    vault_auth_manifest = {
                        "apiVersion": "secrets.hashicorp.com/v1beta1",
                        "kind": "VaultAuth",
                        "metadata": {"name": "placeholder-auth", "namespace": target_ns},
                        "spec": {
                            "method": "kubernetes",
                            "mount": vault_mount,
                            "kubernetes": {
                                "role": vault_role,
                                "serviceAccount": generated_sa_name,
                            },
                        },
                    }
                    if "namespace" in vs_config:
                        vault_auth_manifest["spec"]["namespace"] = vs_config["namespace"]
                    if audiences:
                        vault_auth_manifest["spec"]["kubernetes"]["audiences"] = audiences

                    va_patch_str = yaml.safe_dump(vault_auth_manifest)
                    va_rename = json.dumps(
                        [{"op": "replace", "path": "/metadata/name", "value": default_auth_name}]
                    )
                    sa_rename = json.dumps(
                        [{"op": "replace", "path": "/metadata/name", "value": generated_sa_name}]
                    )

                    auth_source = common_repo.copy()
                    auth_source["path"] = "bootstrap/base/common/vault-resources/auth"
                    apply_patch_to_source(auth_source, va_patch_str, {"kind": "VaultAuth", "name": "placeholder-auth"})
                    apply_patch_to_source(auth_source, va_rename, {"kind": "VaultAuth", "name": "placeholder-auth"})
                    apply_patch_to_source(auth_source, sa_rename, {"kind": "ServiceAccount", "name": "placeholder-sa"})
                    sources.append(auth_source)

            # Create VaultStaticSecrets
            for secret_item in secrets_list:
                vss_manifest = {
                    "apiVersion": "secrets.hashicorp.com/v1beta1",
                    "kind": "VaultStaticSecret",
                    "metadata": {"name": "placeholder-secret", "namespace": target_ns},
                    "spec": {
                        "vaultAuthRef": secret_item.get("auth", default_auth_name),
                        "mount": secret_item.get("mount", "secret"),
                        "type": secret_item.get("type", "kv-v2"),
                        "path": secret_item["path"],
                        "destination": {"name": secret_item["destination"], "create": True},
                    },
                }
                if "refreshInterval" in secret_item:
                    vss_manifest["spec"]["refreshInterval"] = secret_item["refreshInterval"]
                if "namespace" in vs_config:
                    vss_manifest["spec"]["namespace"] = vs_config["namespace"]

                vss_patch_str = yaml.safe_dump(vss_manifest)
                vss_rename = json.dumps(
                    [{"op": "replace", "path": "/metadata/name", "value": secret_item["name"]}]
                )

                secret_source = common_repo.copy()
                secret_source["path"] = "bootstrap/base/common/vault-resources/secret"
                apply_patch_to_source(secret_source, vss_patch_str, {"kind": "VaultStaticSecret", "name": "placeholder-secret"})
                apply_patch_to_source(secret_source, vss_rename, {"kind": "VaultStaticSecret", "name": "placeholder-secret"})
                sources.append(secret_source)

        # === 6. Critical apps (PDB + protection label) ===
        if app_def.get("critical", False):
            if sources:
                primary_src = sources[0]
                if "plugin" not in primary_src:
                    primary_src["plugin"] = {}
                if "env" not in primary_src["plugin"]:
                    primary_src["plugin"]["env"] = []
                primary_src["plugin"]["env"].append(
                    {"name": "ADD_PROTECTED_LABEL", "value": "true"}
                )

            pdb_source = {
                "repoURL": "https://github.com/projectinitiative/homelab.git",
                "targetRevision": "HEAD",
                "path": "bootstrap/base/common/pdb",
            }
            pdb_rename = json.dumps(
                [{"op": "replace", "path": "/metadata/name", "value": f"{app_name}-pdb"}]
            )
            apply_patch_to_source(pdb_source, pdb_rename, {"kind": "PodDisruptionBudget", "name": "critical-cdb-placeholder"})
            sources.append(pdb_source)

        # === 7. Destination ===
        destination = {"server": server_url, "namespace": target_ns}

        # === 8. Sync Policy ===
        default_automated = {"prune": True, "selfHeal": True}
        default_sync_options = ["CreateNamespace=true"]
        app_sync_policy = app_def.get("syncPolicy", {})
        final_automated = app_sync_policy.get("automated", default_automated)
        final_sync_options = app_sync_policy.get("syncOptions", default_sync_options)

        sync_policy = {}
        if final_automated:
            sync_policy["automated"] = final_automated
        if final_sync_options is not None and final_sync_options:
            sync_policy["syncOptions"] = final_sync_options

        if "vaultSecrets" in app_def:
            sync_policy["managedNamespaceMetadata"] = {
                "labels": {"vault-auth": "enabled"}
            }

        # === 9. Construct the Application CR dict ===
        app_manifest = {
            "apiVersion": "argoproj.io/v1alpha1",
            "kind": "Application",
            "metadata": {
                "name": app_name,
                "namespace": argo_namespace,
                "finalizers": ["resources-finalizer.argocd.argoproj.io"],
            },
            "spec": {
                "project": cluster_config.get("project", "default"),
                "sources": sources,
                "destination": destination,
                "syncPolicy": sync_policy,
            },
        }

        if "annotations" in app_def:
            app_manifest["metadata"]["annotations"] = app_def["annotations"]
        if "ignoreDifferences" in app_def:
            app_manifest["spec"]["ignoreDifferences"] = app_def["ignoreDifferences"]

        return app_manifest


# --- Main ---
app = App(outdir=os.environ.get("MANIFEST_OUTPUT_DIR", "dist"))

clusters_files = [
    os.path.join(ROOT_DIR, "clusters/mc.yaml"),
    os.path.join(ROOT_DIR, "clusters/cc.yaml"),
]

for cf in clusters_files:
    if os.path.exists(cf):
        ClusterAppsChart(app, cf)

app.synth()
```

### 3.3 Key Differences from the Pulumi Version

1. **No `recursive_transform`**: cdk8s `ApiObject` accepts camelCase dict keys directly
   (they match Kubernetes API conventions). The Pulumi SDK required snake_case, which is
   why `utils.py` existed. It's now deleted.

2. **No `k8s.Provider`**: cdk8s doesn't need a provider. `App.synth()` writes YAML directly
   to `outdir`. No state, no "unchanged" issues — it always writes all files.

3. **`disable_resource_name_hashes=True`**: cdk8s appends hash suffixes to resource names
   by default (e.g., `mc-kubevirt-c85252a6`). We disable this because we set explicit
   `metadata.name` on every Application CR.

4. **Output format**: cdk8s writes one `{chart-name}.k8s.yaml` file per Chart. With one
   Chart per cluster, the output is:
   ```
   dist/
   ├── mc.k8s.yaml      # All MC cluster Application CRDs
   └── cc.k8s.yaml      # All CC cluster Application CRDs
   ```
   This is different from Pulumi's one-file-per-app format. The CMP reads these with a glob.

### 3.4 Generate cdk8s Manifests

```bash
cd generator
MANIFEST_OUTPUT_DIR=$(pwd)/../snapshot-cdk8s python main.py
```

Verify output:
```bash
ls ../snapshot-cdk8s/
# Expected: mc.k8s.yaml, cc.k8s.yaml
cat ../snapshot-cdk8s/mc.k8s.yaml | head -30  # Verify Application CRDs are present
```

---

## Phase 4: Validation and Diffing

### 4.1 Install `dyff`

`dyff` is a structural YAML diff tool available in nixpkgs. It compares YAML semantically
(ignoring key ordering, whitespace, etc.) rather than line-by-line.

```bash
# Already available in nixpkgs, add to devenv.nix packages if not present
nix run nixpkgs#dyff -- --version
```

### 4.2 Run the Structural Diff

```bash
# The baseline has one file per (cluster, app) — concatenate per cluster
cat snapshot-baseline/mc-*.yaml > /tmp/baseline-mc.yaml
cat snapshot-baseline/cc-*.yaml > /tmp/baseline-cc.yaml

# dyff compares the YAML content, ignoring file boundaries
dyff between --set-exit-code --ignore-order-changes /tmp/baseline-mc.yaml snapshot-cdk8s/mc.k8s.yaml
dyff between --set-exit-code --ignore-order-changes /tmp/baseline-cc.yaml snapshot-cdk8s/cc.k8s.yaml
```

### 4.3 Expected Discrepancies and Fixes

| Discrepancy | Cause | Fix |
|-------------|-------|-----|
| Resource `name` has hash suffix | cdk8s default naming | Verify `disable_resource_name_hashes=True` is set |
| Extra `cdk8s.io/` annotations | cdk8s adds metadata | Use `ApiObject` with `metadata` that doesn't include cdk8s annotations — or add a resolver to strip them |
| Key ordering differences | YAML dump style | `dyff --ignore-order-changes` handles this |
| Missing `apiVersion`/`kind` in output | ApiObject requires both | Verify they're in the dict — they are (hardcoded in `_build_app_manifest`) |

> If `dyff` reports differences in cdk8s-added metadata (like `cdk8s.io/` labels or `app.cdk8s.io/`
> annotations), add a custom `IResolver` to the `App` that strips them:
> ```python
> from cdk8s import IResolver, ResolutionContext
>
> class StripCdk8sMetadataResolver(IResolver):
>     def resolve(self, context: ResolutionContext):
>         # Strip cdk8s.io annotations
>         if "annotations" in str(context.key):
>             annotations = context.obj.annotations or {}
>             filtered = {k: v for k, v in annotations.items() if not k.startswith("cdk8s.io")}
>             context.replace_value(filtered)
>
> app = App(outdir="dist", resolvers=[StripCdk8sMetadataResolver()])
> ```

Resolve all discrepancies until `dyff` returns a clean exit code.

---

## Phase 5: Nix Configuration Updates

### 5.1 Set Up uv2nix for the Generator

The cdk8s/constructs/jsii Python wheels are installed via **uv2nix** (not nixpkgs' Python
package set). uv2nix generates Nix derivations from `generator/uv.lock`.

**Background**: uv2nix is from `github:pyproject-nix/uv2nix`. It requires two flake inputs:
- `uv2nix` — generates Nix derivations from `uv.lock`
- `pyproject-nix` — utilities for parsing `pyproject.toml` (dependency of uv2nix)

These must be added to `flake.nix` inputs (see Phase 5.2 below).

#### 5.1.1 Generator `pyproject.toml`

```toml
# generator/pyproject.toml
[project]
name = "homelab-generator"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "cdk8s>=2.0.0",
    "constructs>=10.0.0",
    "jsii>=1.0.0",
    "pyyaml>=6.0",
]

[tool.uv]
# Lock file at generator/uv.lock (committed to repo)
```

#### 5.1.2 Lock the deps

```bash
cd generator
uv lock
git add uv.lock
```

#### 5.1.3 The `devenv.nix` configuration

Replace Pulumi packages with the cdk8s + uv2nix setup:

```nix
# devenv.nix
{ pkgs, config, lib, ... }:

let
  # uv2nix is wired up in flake.nix as config.uv2nix.packages.<sys>.workspace
  # It exposes a .venv-style environment for the generator
  generatorEnv = config.uv2nix.workspace.generator.env;
in
{
  packages = with pkgs; [
    nodejs                  # REQUIRED: jsii spawns `node` subprocess at runtime
    nodePackages.cdk8s-cli  # For `cdk8s import` (generates Python CRD classes)
    dyff                    # Structural YAML diffing (for diff-manifests)
    uv                      # For regenerating uv.lock when deps change
  ];

  # uv2nix module wiring (configured in flake.nix)
  uv2nix = {
    enable = true;
    workspaces = {
      generator = {
        # Path is relative to project root
        path = ./generator;
        python = pkgs.python311;
      };
    };
  };

  scripts = {
    generate-manifests.exec = ''
      export MANIFEST_OUTPUT_DIR="$PWD/.direnv/manifests"
      mkdir -p "$MANIFEST_OUTPUT_DIR"
      cd generator
      ${generatorEnv}/bin/python main.py
    '';

    import-crds.exec = ''
      cd generator
      ${pkgs.nodePackages.cdk8s-cli}/bin/cdk8s import
    '';

    diff-manifests.exec = ''
      set -e
      PROJECT_ROOT=$(git rev-parse --show-toplevel)
      COMPARE_DIR="$PROJECT_ROOT/.direnv/compare"
      rm -rf "$COMPARE_DIR"
      mkdir -p "$COMPARE_DIR/manifests-current"
      mkdir -p "$COMPARE_DIR/manifests-main"

      # Generate current
      cd "$PROJECT_ROOT/generator"
      MANIFEST_OUTPUT_DIR="$COMPARE_DIR/manifests-current" ${generatorEnv}/bin/python main.py

      # Generate main
      git worktree add --force --detach "$COMPARE_DIR/worktree" origin/main
      cd "$COMPARE_DIR/worktree/generator"
      MANIFEST_OUTPUT_DIR="$COMPARE_DIR/manifests-main" ${generatorEnv}/bin/python main.py

      # Diff
      dyff between --set-exit-code --ignore-order-changes \
        "$COMPARE_DIR/manifests-main/" "$COMPARE_DIR/manifests-current/"

      # Cleanup
      cd "$PROJECT_ROOT"
      git worktree remove --force "$COMPARE_DIR/worktree" || true
    '';
  };

  enterShell = ''
    echo "╔═══════════════════════════════════════════════╗"
    echo "║     Homelab cdk8s Development Shell           ║"
    echo "╚═══════════════════════════════════════════════╝"
    echo ""
    echo "Available commands:"
    echo "  generate-manifests  - Generate Argo CD Application manifests"
    echo "  import-crds         - Import CRDs for cdk8s"
    echo "  diff-manifests      - Diff generated manifests against main"
    echo ""
  '';

  enterTest = ''
    cd generator
    ${generatorEnv}/bin/python -c "from cdk8s import App; print('cdk8s OK')"
    ${generatorEnv}/bin/python -c "from imports.argoproj.io import Application; print('CRD imports OK')"
  '';
}
```

> **Note on `nodejs`**: jsii finds `node` via `PATH` at runtime (via `shutil.which("node")`).
> Adding `nodejs` to `packages` puts `node` on `PATH` in the devenv shell. This is intentional
> and the standard way to satisfy the jsii runtime dependency.
>
> **Note on `cdk8s-cli`**: Only needed for `import-crds` (rarely run — output is committed
> to the repo). The `cdk8s synth` step itself runs `python main.py` directly, no CLI needed.

#### 5.1.4 Verifying the environment

```bash
devenv shell

# Inside the shell:
node --version                # Should print v20.x or later
python -c "import jsii; from cdk8s import App; print('jsii + cdk8s OK')"
python -c "from constructs import Construct; print('constructs OK')"
```

### 5.2 Update `flake.nix`

Update the flake to add uv2nix inputs and remove Pulumi packages.

#### 5.2.1 Add uv2nix flake inputs

```nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";
    flake-parts.inputs.nixpkgs-lib.follows = "nixpkgs";
    devenv.url = "github:cachix/devenv";
    devenv.inputs.nixpkgs.follows = "nixpkgs";
    nix2container.url = "github:nlewo/nix2container";
    nix2container.inputs.nixpkgs.follows = "nixpkgs";
    mk-shell-bin.url = "github:rrbutani/nix-mk-shell-bin";
    ops-utils.url = "github:projectinitiative/ops-utils";
    # NEW: uv2nix for cdk8s/constructs/jsii Python packages
    uv2nix.url = "github:pyproject-nix/uv2nix";
    uv2nix.inputs.nixpkgs.follows = "nixpkgs";
    pyproject-nix.url = "github:pyproject-nix/pyproject.nix";
    pyproject-nix.inputs.nixpkgs.follows = "nixpkgs";
  };
  # ...
}
```

#### 5.2.2 Wire uv2nix into the devenv module

In the `perSystem` block, register the generator workspace so uv2nix builds the Python
environment from `generator/uv.lock`:

```nix
perSystem = { config, pkgs, lib, system, ... }:
let
  # ... (existing ops-utils, etc.)

  # The uv2nix-generated environment for the generator
  # Available as config.uv2nix.workspace.generator.env (used in devenv.nix)
  # uv2nix module handles the actual derivation from generator/uv.lock

  # For the CMP image: build the same Python env using uv2nix's lower-level API
  # so it's hermetic (no Node.js-via-PATH needed inside the image — we add nodejs
  # to contents explicitly)
  generatorPyEnv = config.uv2nix.workspace.generator.env;
in {
  packages = {
    # REMOVE all Pulumi packages:
    #   pulumi-cmp-plugin, pulumi-cmp-plugin-arm-cross, import-crds (pulumi),
    #   generate-manifests (pulumi), setup-pulumi

    # NEW: cdk8s CMP image
    cmp-image = import ./generator/cmp-image/image.nix {
      inherit pkgs;
      pythonEnv = generatorPyEnv;
    };

    # NEW: cdk8s CMP image (ARM cross-compile for MC cluster nodes)
    cmp-image-arm-cross =
      if system == "x86_64-linux"
      then import ./generator/cmp-image/image.nix {
        pkgs = pkgsCrossARM;
        pythonEnv = generatorPyEnvCross;  # Use uv2nix for cross-build
      }
      else config.packages.cmp-image;

    # NEW scripts (devenv.nix also has these inline, but flake exposes them for `nix run`)
    generate-manifests = import ./nix/scripts/generate-manifests.nix {
      inherit pkgs;
      pythonEnv = generatorPyEnv;
    };

    import-crds = import ./nix/scripts/import-crds.nix { inherit pkgs; };
    diff-manifests = import ./nix/scripts/diff-manifests.nix { inherit pkgs; };
  };

  # Register uv2nix workspaces (consumed by devenv.nix)
  uv2nix = {
    workspaces.generator = {
      path = ./generator;
      python = pkgs.python311;
    };
  };

  devenv.shells.default = {
    imports = [ ./devenv.nix ];
    devenv.root = lib.mkForce (toString ./.);
  };
  # ...
};
```

#### 5.2.3 Cross-compilation note

For the ARM CMP image (`cmp-image-arm-cross`), uv2nix needs `pkgsCrossARM`. uv2nix generates
Python derivations that should be portable — jsii/cdk8s/constructs are pure Python (the bundled
JS bundle is platform-independent). The only platform-specific piece is `nodejs` for the runtime
subprocess, which we add separately via `pkgs.nodejs` (or `pkgsCrossARM.nodejs`).

If cross-compilation proves problematic, fallback to building the CMP image natively for x86_64
and using multi-arch Docker manifests — see Go fallback in Phase 8.

### 5.3 Update `nix/scripts/generate-manifests.nix`

```nix
{ pkgs, pythonEnv }:
pkgs.writeShellScriptBin "generate-manifests" ''
  set -e
  export PATH="${pythonEnv}/bin:${pkgs.nodejs}/bin:$PATH"

  if [ -z "$MANIFEST_OUTPUT_DIR" ]; then
    export MANIFEST_OUTPUT_DIR=$(pwd)/.direnv/manifests
  fi
  mkdir -p "$MANIFEST_OUTPUT_DIR"

  echo "Generating manifests to $MANIFEST_OUTPUT_DIR..."
  cd generator
  ${pythonEnv}/bin/python main.py
  echo "✅ Manifests generated in $MANIFEST_OUTPUT_DIR"
''
```

> Note: `${pkgs.nodejs}/bin` is on PATH so jsii can spawn `node` at synth time.

### 5.4 Update `nix/scripts/import-crds.nix`

```nix
{ pkgs }:
pkgs.writeShellScriptBin "import-crds" ''
  set -e
  cd generator
  ${pkgs.nodePackages.cdk8s-cli}/bin/cdk8s import
  echo "✅ CRDs imported to generator/imports/"
''
```

---

## Phase 6: CMP Image Cutover

### 6.1 Create `generator/cmp-image/image.nix`

The CMP image runs inside the Argo CD repo server. The `pythonEnv` passed in is the
**uv2nix-generated environment** (from `config.uv2nix.workspace.generator.env` in `flake.nix`),
which is a fully hermetic Nix store path containing `cdk8s`, `constructs`, `jsii`, and
all their transitive Python dependencies.

```nix
# generator/cmp-image/image.nix
{ pkgs, pythonEnv }:

let
  # The generator script: runs `python main.py` (cdk8s synth)
  # and concatenates the output YAML to stdout (captured by Argo CD)
  cdk8sGenerate = pkgs.writeShellScriptBin "cdk8s-generate" ''
    export HOME=/home/argocd
    # pythonEnv contains all Python deps; nodejs is needed for jsii subprocess
    export PATH=${pythonEnv}/bin:${pkgs.nodejs}/bin:$PATH
    cd /app/generator
    ${pythonEnv}/bin/python main.py 1>&2
    # cdk8s writes YAML to dist/*.k8s.yaml — concatenate for Argo CD
    cat /app/generator/dist/*.k8s.yaml
  '';

in pkgs.dockerTools.buildLayeredImage {
  name = "cdk8s-cmp-plugin";
  tag = "latest";

  config = {
    Env = [
      "PATH=/bin"
      "HOME=/home/argocd"
    ];
    User = "999";
    WorkingDir = "/app/generator";
  };

  # contents = layers added to the image
  contents = [
    pkgs.cacert
    pkgs.nodejs          # REQUIRED: jsii spawns `node` subprocess at synth time
    pythonEnv            # The uv2nix-generated Python env (cdk8s, constructs, jsii, pyyaml)
    pkgs.bash
    pkgs.coreutils
    pkgs.fakeNss
    cdk8sGenerate
  ];

  fakeRootCommands = ''
    mkdir -p ./home/argocd
    mkdir -p ./app/generator
    chmod 1777 ./tmp
    chown -R 999:999 ./home/argocd
  '';
}
```

#### 6.1.1 How this works

1. uv2nix builds the Python environment (transitively pulls `jsii`, `cdk8s`, `constructs`,
   `pyyaml` and their deps) from `generator/uv.lock`. The result is a Nix store path
   like `/nix/store/xxx-python3.11-with-packages`.
2. The Python wheels ship with their bundled JS bundles (in `wheel_data/jsii/_runtime/`).
   uv2nix copies them verbatim — no execution at build time.
3. At runtime, the container runs `python main.py` → calls `app.synth()` → jsii finds
   `node` via `PATH` (we add `pkgs.nodejs` to `contents`) and spawns the JS runtime.
4. Output YAML files appear in `dist/` and the wrapper script cats them to stdout for
   Argo CD to consume.

#### 6.1.2 Build-time Node.js vs runtime Node.js

uv2nix does NOT need Node.js at build time — jsii as a Python package is a pure wheel
(no compilation step). Node.js is only a **runtime** subprocess dependency.

### 6.2 (Deleted — no longer needed)

The original Phase 6.2 described workarounds for installing Python deps inside the image.
With uv2nix, this is automatic — `pythonEnv` from the flake carries all Python packages.

### 6.3 Update Argo CD CMP ConfigMap

Update the CMP plugin configuration in `argocd-deployment/` to reference the new image
and generation script. The plugin name changes from `pulumi-v1.0` to `cdk8s-v1.0`.

### 6.4 Update GitHub Actions

Update `build-push-pulumi-cmp.yaml` → `build-push-cdk8s-cmp.yaml`:
- Change the image name from `pulumi-cmp-plugin` to `cdk8s-cmp-plugin`
- Update build paths from `pulumi/cmp-image/` to `generator/cmp-image/`
- The Docker build process stays the same (Nix + nix2container)

---

## Phase 7: Cleanup

### 7.1 Delete Pulumi Artifacts

```bash
rm -rf pulumi/                    # The entire Pulumi directory
rm -f nix/scripts/generate-manifests.nix   # Old version (replaced)
rm -f nix/scripts/setup-pulumi.nix
rm -f nix/scripts/import-crds.nix           # Old version (replaced)
rm -rf ~/.pulumi/                # Local Pulumi state
rm -rf .direnv/manifests/        # Old empty directories from Pulumi
```

### 7.2 Update `.gitignore`

Remove Pulumi-specific entries, add cdk8s-specific ones:

```gitignore
# Remove:
# .pulumi/

# Add:
generator/dist/
generator/.venv/
.direnv/manifests/
.direnv/compare/
```

### 7.3 Update `AGENTS.md`

Update the architecture documentation to reflect the cdk8s-based generator:

- Replace references to `pulumi/__main__.py` with `generator/main.py`
- Replace references to `pulumi/crds/` with `generator/imports/`
- Replace references to `crd2pulumi` with `cdk8s import`
- Replace the "Pulumi Generation Engine" section with "cdk8s Generation Engine"
- Update the patch system diagram to show cdk8s instead of Pulumi
- Remove references to Pulumi state, stacks, and `pulumi up`

### 7.4 Update `flake.nix`

Remove all Pulumi-related inputs and packages:
- Remove `pulumi` from `packages`
- Remove `pulumiPackages.pulumi-python` from packages
- Remove `crd2pulumi` from packages
- Remove `mkPulumiEnv` helper and all `pulumi_crds` build logic
- Remove cross-compilation for ARM Pulumi (if cdk8s supports ARM natively via Node.js)

---

## Phase 8: Future Extensibility (Construct Composition)

### 8.1 Why cdk8s Enables This

cdk8s is built on the `constructs` library (v10.x). Any `Construct` subclass can be:
1. Defined in one repo
2. Published as a Python package to PyPI (or a private registry)
3. Imported and used in any other cdk8s project

This means you can create reusable cdk8s libraries for common patterns:
- A "homelab-base" library with common labels, annotations, and namespace conventions
- A "vault-integration" library with VaultAuth/VaultStaticSecret constructs
- An "argo-application" library (which this generator effectively is)

### 8.2 Example: Publishing a Construct Library

```python
# In a separate repo (e.g., homelab-cdk8s-constructs)
from constructs import Construct
from cdk8s import Chart
from imports.argoproj.io import Application

class VaultSecuredApp(Construct):
    """Reusable construct: creates an Argo CD Application with vault secrets."""

    def __init__(self, scope: Construct, id: str, *,
                 app_name: str, namespace: str, vault_mount: str,
                 vault_path: str, sources: list, **kwargs):
        super().__init__(scope, id)
        # ... construct Application + VaultAuth + VaultStaticSecret ...
```

### 8.3 Importing in Another Repo

```python
# In another cdk8s project's main.py
from homelab_cdk8s_constructs import VaultSecuredApp

app = App()
chart = Chart(app, "my-apps")
VaultSecuredApp(chart, "my-secured-app",
    app_name="my-app",
    namespace="my-namespace",
    vault_mount="kubernetes_cluster_mc",
    vault_path="my-app/credentials",
    sources=[...],
)
app.synth()
```

### 8.4 Using cdk8s+ for Application Definitions

cdk8s+ provides high-level abstractions for defining actual Kubernetes resources:

```python
from cdk8s_plus_34 import Deployment, Container, Service

# Instead of raw YAML, define apps programmatically:
Deployment(chart, "my-app",
    containers=[Container(image="nginx:1.25", port=80)],
    replicas=3,
)
Service(chart, "my-app-service", selector={"app": "my-app"}, ports=[{"port": 80}])
```

This could replace Helm charts for simple apps in the future.

---

## Phase 9: Go Fallback (if jsii proves too fragile)

If the jsii + Node.js path encounters insurmountable issues (e.g., CMP image bloat from
Node.js, ARM cross-compilation problems with the jsii runtime, performance issues from
subprocess spawning on every CMP invocation), the generator can be rewritten using the
**cdk8s Go SDK**.

### 9.1 Why Go is the fallback

- **Native single binary**: No Node.js, no Python, no subprocess, no jsii bridge
- **All cdk8s features**: Charts, ApiObject, `cdk8s import`, construct composition
  (cdk8s Go uses the same `constructs` library — just native Go, not jsii-bridged)
- **Excellent Nix support**: `buildGoModule` is well-trodden territory in nixpkgs
- **Construct sharing**: Works via Go modules (`go get`) instead of pip packages

### 9.2 Migration path from Python to Go

1. Keep `apps.yaml` and `clusters/*.yaml` as-is (no changes to the declarative config)
2. Port the dict-construction logic from `generator/main.py` to `generator/main.go`
3. Replace `cdk8s import` (Python classes) with `cdk8s import` (Go structs in `imports/`)
4. Replace `pyyaml` with `gopkg.in/yaml.v3` for parsing the config files
5. `cdk8s synth` runs `go run main.go` natively — fast startup, no subprocess overhead

### 9.3 Simplified CMP image for Go

```nix
generatorBinary = pkgs.buildGoModule {
  name = "homelab-cdk8s-generator";
  src = ./generator;
  vendorHash = "sha256-...";  # From `nix build` first attempt
  subPackages = [ "." ];
};

# CMP image is tiny — just one static binary + CA certs
cmpImage = pkgs.dockerTools.buildLayeredImage {
  name = "cdk8s-cmp-plugin";
  contents = [ pkgs.cacert generatorBinary ];
  config.WorkingDir = "/app";
};
```

No Node.js layer, no Python env layer, no uv2nix — just a single Go binary and CA certs.

### 9.4 When to trigger the fallback

Switch to the Go path if:
- The CMP image exceeds ~500MB due to Node.js runtime
- jsii subprocess spawning adds >5s to every CMP invocation
- ARM cross-compilation of Node.js fails repeatedly
- jsii version conflicts between cdk8s releases (has happened historically)

Until then, the Python + uv2nix path in Phases 1-7 is the primary implementation.

---

## Validation Checklist

- [x] Phase 1: Baseline snapshot generated (44 files in `snapshot-baseline/`)
- [x] Phase 2: cdk8s environment works (`python -c "from cdk8s import App"` succeeds)
- [x] Phase 2: CRDs imported (`generator/imports/` has argoproj and secrets dirs)
- [x] Phase 3: cdk8s generates manifests (`mc.k8s.yaml` and `cc.k8s.yaml` exist)
- [x] Phase 4: All 44 apps match 1:1 between Pulumi baseline and cdk8s output (0 differences)
- [x] Phase 5: uv2nix builds hermetic `pythonEnv` from `generator/uv.lock` (no `uv sync` at runtime)
- [x] Phase 5: `nix flake check --no-build` passes with zero errors
- [x] Phase 5: `nix run .#generate-manifests` works end-to-end
- [ ] Phase 5: `devenv shell` / `direnv reload` works (user to validate)
- [ ] Phase 5: `diff-manifests` works against `main` branch (user to validate)
- [ ] Phase 6: CMP image builds (uv2nix env + Node.js layer inside the image)
- [ ] Phase 6: Argo CD picks up the new CMP and deploys apps (including kubevirt)
- [x] Phase 7: `pulumi/` directory deleted, no references remain
- [x] Phase 7: `AGENTS.md` updated to reflect cdk8s architecture

---

## How to Validate the Migration (1:1 Manifest Comparison)

The cdk8s generator **must produce byte-identical Application CRDs** as the old Pulumi
generator. Both read the same `apps.yaml` + `clusters/*.yaml` and produce the same
Argo CD `Application` resources. Validation is straightforward:

### Prerequisites

You need both the old (Pulumi) and new (cdk8s) outputs. The old output was captured
as a baseline before the migration. If `snapshot-baseline/` doesn't exist, regenerate
it from the `main` branch (before this migration):

```bash
# 1. Checkout main (has the old Pulumi generator)
git checkout main

# 2. Patch pulumi/__main__.py to bypass the broken Pulumi v4 provider
#    (See Phase 1.1 in this doc — the key change is removing pulumi imports
#     and writing YAML directly via yaml.safe_dump)

# 3. Generate the baseline snapshot
mkdir -p snapshot-baseline
cd pulumi
MANIFEST_OUTPUT_DIR=../snapshot-baseline python3 __main__.py
```

### Step-by-step: Compare old vs new

```bash
# Checkout the migration branch
git checkout migrate-to-cdk8s

# 1. Generate cdk8s manifests (hermetic, via uv2nix)
nix run .#generate-manifests
# Output: .direnv/manifests/mc.k8s.yaml, .direnv/manifests/cc.k8s.yaml
# (one multi-document YAML per cluster)

# 2. The baseline has one file per (cluster, app), e.g.:
#    snapshot-baseline/mc-kube-vip-app.yaml, snapshot-baseline/mc-openbao.yaml, etc.
#    The cdk8s output has one file per cluster with all apps inside.
#    Both contain the exact same Application CRDs — just different file organization.

# 3. Structural diff using dyff (semantically compares YAML, ignores key ordering)
#    Concatenate baseline per-cluster, then diff:
cat snapshot-baseline/mc-*.yaml > /tmp/baseline-mc.yaml
cat snapshot-baseline/cc-*.yaml > /tmp/baseline-cc.yaml

#    Sort both sides by metadata.name so dyff matches documents correctly:
python3 -c "
import yaml, sys
docs = sorted(yaml.safe_load_all(open(sys.argv[1])), key=lambda d: d['metadata']['name'])
yaml.safe_dump_all(docs, sys.stdout, default_flow_style=False, sort_keys=False, explicit_start=True)
" /tmp/baseline-mc.yaml > /tmp/baseline-mc-sorted.yaml
python3 -c "
import yaml, sys
docs = sorted(yaml.safe_load_all(open(sys.argv[1])), key=lambda d: d['metadata']['name'])
yaml.safe_dump_all(docs, sys.stdout, default_flow_style=False, sort_keys=False, explicit_start=True)
" .direnv/manifests/mc.k8s.yaml > /tmp/cdk8s-mc-sorted.yaml

nix run nixpkgs#dyff -- between --set-exit-code --ignore-order-changes \
  /tmp/baseline-mc-sorted.yaml /tmp/cdk8s-mc-sorted.yaml

# Repeat for cc:
python3 -c "
import yaml, sys
docs = sorted(yaml.safe_load_all(open(sys.argv[1])), key=lambda d: d['metadata']['name'])
yaml.safe_dump_all(docs, sys.stdout, default_flow_style=False, sort_keys=False, explicit_start=True)
" /tmp/baseline-cc.yaml > /tmp/baseline-cc-sorted.yaml
python3 -c "
import yaml, sys
docs = sorted(yaml.safe_load_all(open(sys.argv[1])), key=lambda d: d['metadata']['name'])
yaml.safe_dump_all(docs, sys.stdout, default_flow_style=False, sort_keys=False, explicit_start=True)
" .direnv/manifests/cc.k8s.yaml > /tmp/cdk8s-cc-sorted.yaml

nix run nixpkgs#dyff -- between --set-exit-code --ignore-order-changes \
  /tmp/baseline-cc-sorted.yaml /tmp/cdk8s-cc-sorted.yaml
```

**Expected result:** `dyff` reports zero differences for both clusters. This was
verified during the migration: all 44 apps (28 mc + 16 cc) match 1:1.

### Quick programmatic comparison

For a faster check, use this Python script to compare documents by `metadata.name`
(no sorting or dyff needed):

```python
#!/usr/bin/env python3
import yaml
import os
import sys

BASELINE_GLOB = sys.argv[1]  # e.g. "snapshot-baseline/mc-*"
CDK8S_FILE = sys.argv[2]     # e.g. ".direnv/manifests/mc.k8s.yaml"

# Load cdk8s multi-doc file
with open(CDK8S_FILE) as f:
    cdk8s_docs = {d["metadata"]["name"]: d for d in yaml.safe_load_all(f) if d}

# Load baseline (one file per app)
baseline_docs = {}
for fname in sorted(os.listdir(os.path.dirname(BASELINE_GLOB))):
    if not fname.startswith(os.path.basename(BASELINE_GLOB).replace("*", "")):
        continue
    with open(os.path.join(os.path.dirname(BASELINE_GLOB), fname)) as f:
        doc = yaml.safe_load(f)
    baseline_docs[doc["metadata"]["name"]] = doc

# Compare
diffs = 0
for name in sorted(set(baseline_docs) | set(cdk8s_docs)):
    if name not in cdk8s_docs:
        print(f"  MISSING in cdk8s: {name}")
        diffs += 1
    elif name not in baseline_docs:
        print(f"  EXTRA in cdk8s: {name}")
        diffs += 1
    elif baseline_docs[name] != cdk8s_docs[name]:
        print(f"  DIFF: {name}")
        diffs += 1

print(f"\n{len(baseline_docs)} baseline, {len(cdk8s_docs)} cdk8s, {diffs} differences")
sys.exit(1 if diffs else 0)
```

### Validating with `diff-manifests` (against main branch)

Once the migration is merged to `main`, the `diff-manifests` command compares
the current working tree against `origin/main`:

```bash
# In the devenv shell:
diff-manifests

# Or via nix:
nix run .#diff-manifests
```

This checks out `origin/main` to a worktree, generates manifests from both trees
using the same uv2nix `pythonEnv`, and runs `dyff` between them.

### What "1:1" means

Every Application CRD must be **structurally identical**:
- Same `metadata.name`, `metadata.namespace`, `metadata.finalizers`, `metadata.annotations`
- Same `spec.project`, `spec.sources` (including kustomize patches, helm values, plugin env)
- Same `spec.destination`, `spec.syncPolicy` (including `managedNamespaceMetadata`)
- Same `spec.ignoreDifferences`

Minor YAML formatting differences (key ordering, quoting style, list indentation) are
acceptable and ignored by `dyff --ignore-order-changes`.

### Files changed in the migration

| Before (Pulumi) | After (cdk8s) |
|-----------------|---------------|
| `pulumi/__main__.py` | `generator/main.py` |
| `pulumi/utils.py` | (deleted — not needed, cdk8s accepts camelCase) |
| `pulumi/crd-imports.json` | `generator/cdk8s.yaml` |
| `pulumi/crds/pulumi_crds/` | `generator/imports/` |
| `pulumi/cmp-image/image.nix` | `generator/cmp-image/image.nix` |
| `pulumi/pyproject.toml` | `generator/pyproject.toml` |
| (none) | `generator/uv.lock` |
| `flake.nix` (pulumi deps) | `flake.nix` (uv2nix + pyproject-nix inputs) |
| `devenv.nix` (pulumi) | `devenv.nix` (cdk8s + uv2nix via packages) |

---

## Rollback Plan

If the cdk8s migration reveals issues that can't be resolved quickly:

1. **Revert this branch** — `git checkout main` restores the Pulumi generator
2. The patched `pulumi/__main__.py` (Phase 1, writing YAML directly) can be applied
   to `main` as a hotfix if the broken `render_yaml_to_directory` is still an issue
3. `pulumi/` directory still exists on `main` — no data loss

**Note:** The `pulumi/` directory was deleted on this branch. The old code is
preserved on the `main` branch until this migration is validated and merged.

