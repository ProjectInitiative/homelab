#!/usr/bin/env python3
"""Homelab Argo CD Application manifest generator (cdk8s)."""

import yaml
import json
import os
import sys
import copy

from cdk8s import App, Chart, ApiObject, JsonPatch
from constructs import Construct


def load_yaml(path):
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return yaml.safe_load(f)


# --- Config paths ---
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

            obj = ApiObject(
                self,
                f"{cluster_name}-{app_name}",
                api_version=app_manifest["apiVersion"],
                kind=app_manifest["kind"],
                metadata=app_manifest["metadata"],
            )
            obj.add_json_patch(JsonPatch.add("/spec", app_manifest["spec"]))

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
        """Construct the Application CR dict."""
        # === 1. Source(s) ===
        sources = []
        if "sources" in app_def:
            sources = copy.deepcopy(app_def["sources"])
        else:
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
            apply_patch_to_source(pdb_source, pdb_rename, {"kind": "PodDisruptionBudget", "name": "critical-pdb-placeholder"})
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
