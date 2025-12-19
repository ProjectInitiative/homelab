import pulumi
import pulumi_kubernetes as k8s
import yaml
import json
import os
import sys
import copy

# Add the generated CRDs to the python path
sys.path.append(os.path.join(os.getcwd(), 'crds'))

try:
    from pulumi_crds.argoproj.v1alpha1 import Application
except ImportError as e:
    print(f"Error importing generated CRDs: {e}", file=sys.stderr)
    print("Make sure you have run 'import-crds pulumi/crd-imports.json' and the 'crds' directory exists.", file=sys.stderr)
    sys.exit(1)

from utils import recursive_transform

def load_yaml(path):
    if not os.path.exists(path):
        return None
    with open(path, 'r') as f:
        return yaml.safe_load(f)

# Config paths
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
apps_catalog_file = os.path.join(root_dir, "apps.yaml")
apps_catalog = load_yaml(apps_catalog_file)

if not apps_catalog:
    print(f"Error: apps.yaml not found at {apps_catalog_file}", file=sys.stderr)
    sys.exit(1)

defaults = apps_catalog.get('defaults', {})
catalog = apps_catalog.get('catalog', {})

# Configure the provider to render YAML to a local directory
render_dir = os.environ.get("PULUMI_MANIFEST_OUTPUT_DIR", os.path.join(os.getcwd(), "manifests"))
k8s_provider = k8s.Provider("k8s-yaml-renderer", 
    render_yaml_to_directory=render_dir
)

def process_cluster(cluster_file):
    cluster_config = load_yaml(cluster_file)
    if not cluster_config:
        return

    cluster_name = cluster_config['name']
    server_url = cluster_config['server']
    argo_namespace = cluster_config['argoNamespace']
    
    print(f"Processing cluster: {cluster_name} ({server_url})", file=sys.stderr)

    vault_mount = cluster_config.get('vaultMount')

    apps = cluster_config.get('apps', [])
    for app_deployment in apps:
        app_name = app_deployment['name']
        
        # Lookup app in catalog
        app_def = catalog.get(app_name)
        if not app_def:
            print(f"  [WARN] App '{app_name}' not found in apps.yaml catalog. Skipping.", file=sys.stderr)
            continue

        target_ns = app_deployment.get('namespace')
        if not target_ns:
             print(f"  [WARN] Namespace not specified for '{app_name}' in {cluster_name}. Skipping.", file=sys.stderr)
             continue

        print(f"  Generating '{app_name}' for '{target_ns}'", file=sys.stderr)

        # Build Application Spec
        # 1. Source(s)
        sources = []
        if 'sources' in app_def:
            sources = copy.deepcopy(app_def['sources'])
        else:
            # Legacy single source construction
            source = {
                'repoURL': app_def.get('repoURL', defaults.get('repoURL')),
                'targetRevision': app_def.get('targetRevision', defaults.get('targetRevision')),
                'path': app_def.get('path'),
                'chart': app_def.get('chart')
            }
            if 'directory' in app_def:
                source['directory'] = app_def['directory']
            
            # Add plugin field if present in app_def
            if 'plugin' in app_def:
                source['plugin'] = app_def['plugin']
            
            # Remove None values
            source = {k: v for k, v in source.items() if v is not None}
            sources = [source]

        # Overrides from Deployment (e.g. patches, Helm values)
        # We apply these to the FIRST source in the list by default,
        # or the one that makes sense (e.g. helm values apply to the helm source).
        
        # Handle Kustomize patches
        
        # Helper function to apply a patch to a specific source
        def apply_patch_to_source(src_obj, patch_content, patch_target=None):
            if 'kustomize' not in src_obj:
                src_obj['kustomize'] = {}
            
            patch_entry = {'patch': patch_content}
            if patch_target:
                patch_entry['target'] = patch_target
            
            if 'patches' not in src_obj['kustomize']:
                src_obj['kustomize']['patches'] = []
            src_obj['kustomize']['patches'].append(patch_entry)

        # 1. Legacy/Single Patch Support (top-level 'patch' field)
        if 'patch' in app_deployment and app_deployment['patch']:
            # Determine target source for this legacy patch
            legacy_target_source = None
            
            if 'patchSourceIndex' in app_deployment:
                idx = app_deployment['patchSourceIndex']
                if 0 <= idx < len(sources):
                    legacy_target_source = sources[idx]
                else:
                    print(f"  [WARN] patchSourceIndex {idx} out of bounds for '{app_name}'.", file=sys.stderr)
            
            # Fallback heuristic if not set by index
            if legacy_target_source is None:
                for src in sources:
                    if 'path' in src and (src.get('path', '').endswith('config') or 'kustomize' in src):
                        legacy_target_source = src
                        break # Use the first matching config source
                
                if legacy_target_source is None:
                    legacy_target_source = sources[0]

            apply_patch_to_source(legacy_target_source, app_deployment['patch'], app_deployment.get('patchTarget'))

        # 2. Multi-Patch Support (new 'patches' list)
        if 'patches' in app_deployment and isinstance(app_deployment['patches'], list):
            for p in app_deployment['patches']:
                if 'patch' not in p: 
                    continue
                
                patch_src_idx = p.get('sourceIndex', 0) # Default to 0 if not specified
                target_src = None
                
                if 0 <= patch_src_idx < len(sources):
                    target_src = sources[patch_src_idx]
                else:
                    print(f"  [WARN] patches sourceIndex {patch_src_idx} out of bounds for '{app_name}'.", file=sys.stderr)
                    continue # Skip this patch
                
                apply_patch_to_source(target_src, p['patch'], p.get('target'))


        # Handle Helm (Values)
        # Similar logic could be applied here if we needed multi-source Helm values, 
        # but for now we keep the single target logic for Helm values.
        
        target_source_for_helm_values = None
        if 'helmValuesSourceIndex' in app_deployment:
             idx = app_deployment['helmValuesSourceIndex']
             if 0 <= idx < len(sources):
                 target_source_for_helm_values = sources[idx]
        
        if target_source_for_helm_values is None:
             for src in sources:
                if 'chart' in src and 'helm' in src:
                    target_source_for_helm_values = src
        
        if target_source_for_helm_values is None:
            target_source_for_helm_values = sources[0]

        if 'helm_values' in app_deployment or 'value_files' in app_deployment:
            if 'helm' not in target_source_for_helm_values:
                target_source_for_helm_values['helm'] = {}
            
            if 'helm_values' in app_deployment:
                target_source_for_helm_values['helm']['values'] = app_deployment['helm_values']
            if 'value_files' in app_deployment:
                existing_value_files = target_source_for_helm_values['helm'].get('valueFiles', [])
                if not isinstance(existing_value_files, list):
                    existing_value_files = [existing_value_files] # Ensure it's a list
                new_value_files = app_deployment['value_files']
                if not isinstance(new_value_files, list):
                    new_value_files = [new_value_files]
                target_source_for_helm_values['helm']['valueFiles'] = existing_value_files + new_value_files

        # Handle Vault Secrets (Auto-Injection)
        if 'vaultSecrets' in app_def:
            vs_config = app_def['vaultSecrets']
            secrets_list = vs_config.get('secrets', [])
            
            # Default Auth Method name
            default_auth_name = vs_config.get('auth', 'operator-auth')
            
            # Source for our common vault resources (auto-injected)
            common_vault_resources_repo = {
                'repoURL': 'https://github.com/projectinitiative/homelab.git', # Self-reference
                'targetRevision': 'HEAD',
            }

            # 1. Auto-Create VaultAuth
            if vs_config.get('createAuth', False):
                 if not vault_mount:
                     print(f"  [WARN] 'createAuth' is True for '{app_name}' but 'vaultMount' is not defined in cluster '{cluster_name}'. Skipping VaultAuth generation.", file=sys.stderr)
                 else:
                     vault_role = vs_config.get('role', 'openbao-secrets-operator')
                     # We generate a dedicated SA: {auth_name}-sa
                     generated_sa_name = f"{default_auth_name}-sa"
                     audiences = vs_config.get('audiences', [])
                     
                     # 1. VaultAuth Spec Patch
                     vault_auth_manifest = {
                        'apiVersion': 'secrets.hashicorp.com/v1beta1',
                        'kind': 'VaultAuth',
                        'metadata': {
                            'name': 'placeholder-auth', 
                            'namespace': target_ns
                        },
                        'spec': {
                            'method': 'kubernetes',
                            'mount': vault_mount,
                            'kubernetes': {
                                'role': vault_role,
                                'serviceAccount': generated_sa_name
                            }
                        }
                     }
                     
                     if 'namespace' in vs_config:
                         vault_auth_manifest['spec']['namespace'] = vs_config['namespace']
                     
                     if audiences:
                         vault_auth_manifest['spec']['kubernetes']['audiences'] = audiences
                     
                     va_patch_str = yaml.safe_dump(vault_auth_manifest)
                     
                     # 2. VaultAuth Rename Patch
                     va_rename_patch = json.dumps([
                         {"op": "replace", "path": "/metadata/name", "value": default_auth_name}
                     ])

                     # 3. ServiceAccount Rename Patch
                     # We rename 'placeholder-sa' to 'operator-auth-sa'
                     sa_rename_patch = json.dumps([
                         {"op": "replace", "path": "/metadata/name", "value": generated_sa_name}
                     ])
                     
                     # Add Source
                     auth_source = common_vault_resources_repo.copy()
                     auth_source['path'] = 'bootstrap/base/common/vault-resources/auth'
                     
                     # Apply Patches
                     apply_patch_to_source(auth_source, va_patch_str, {'kind': 'VaultAuth', 'name': 'placeholder-auth'})
                     apply_patch_to_source(auth_source, va_rename_patch, {'kind': 'VaultAuth', 'name': 'placeholder-auth'})
                     apply_patch_to_source(auth_source, sa_rename_patch, {'kind': 'ServiceAccount', 'name': 'placeholder-sa'})
                     
                     sources.append(auth_source)

            # 2. Create VaultStaticSecrets (one source per secret)
            for secret_item in secrets_list:
                # YAML Patch for Spec and Namespace
                vss_manifest = {
                    'apiVersion': 'secrets.hashicorp.com/v1beta1',
                    'kind': 'VaultStaticSecret',
                    'metadata': {
                        'name': 'placeholder-secret', # Must match target for valid patch parsing
                        'namespace': target_ns 
                    },
                    'spec': {
                        'vaultAuthRef': secret_item.get('auth', default_auth_name),
                        'mount': secret_item.get('mount', 'secret'), # Default mount point
                        'type': secret_item.get('type', 'kv-v2'), # Vault Secret Type
                        'path': secret_item['path'],
                        'destination': {
                            'name': secret_item['destination'],
                            'create': True
                        }
                    }
                }
                
                if 'refreshInterval' in secret_item:
                    vss_manifest['spec']['refreshInterval'] = secret_item['refreshInterval']

                if 'namespace' in vs_config:
                    vss_manifest['spec']['namespace'] = vs_config['namespace']

                vss_patch_str = yaml.safe_dump(vss_manifest)
                
                # JSON Patch for Renaming
                vss_rename_patch = json.dumps([
                    {"op": "replace", "path": "/metadata/name", "value": secret_item['name']}
                ])

                # Add a source for each VaultStaticSecret resource and patch it
                secret_source = common_vault_resources_repo.copy()
                secret_source['path'] = 'bootstrap/base/common/vault-resources/secret'
                
                # Apply Spec Patch
                apply_patch_to_source(secret_source, vss_patch_str, {'kind': 'VaultStaticSecret', 'name': 'placeholder-secret'})
                # Apply Rename Patch
                apply_patch_to_source(secret_source, vss_rename_patch, {'kind': 'VaultStaticSecret', 'name': 'placeholder-secret'})

                sources.append(secret_source)
        # 2. Destination
        destination = {
            'server': server_url,
            'namespace': target_ns
        }

        # 3. Sync Policy
        # Defaults
        default_automated = {'prune': True, 'selfHeal': True}
        default_sync_options = ['CreateNamespace=true']

        # Get app-specific overrides
        app_sync_policy = app_def.get('syncPolicy', {})
        
        # Determine final values (App overrides default)
        final_automated = app_sync_policy.get('automated', default_automated)
        final_sync_options = app_sync_policy.get('syncOptions', default_sync_options)

        sync_policy = {}
        if final_automated:
            sync_policy['automated'] = final_automated
        
        # Only include syncOptions if it's a non-empty list or explicitly not None
        if final_sync_options is not None and final_sync_options:
            sync_policy['syncOptions'] = final_sync_options

        # Manage Namespace Metadata for Vault Auth
        # If the app uses Vault Secrets, automatically label the namespace
        if 'vaultSecrets' in app_def:
             sync_policy['managedNamespaceMetadata'] = {
                 'labels': {
                     'vault-auth': 'enabled'
                 }
             }

        # Construct the Application CR dict
        app_manifest = {
            'apiVersion': 'argoproj.io/v1alpha1',
            'kind': 'Application',
            'metadata': {
                'name': app_name, 
                'namespace': argo_namespace,
                'finalizers': ['resources-finalizer.argocd.argoproj.io']
            },
            'spec': {
                'project': cluster_config.get('project', 'default'),
                'sources': sources,
                'destination': destination,
                'syncPolicy': sync_policy
            }
        }

        if 'annotations' in app_def:
            app_manifest['metadata']['annotations'] = app_def['annotations']
        
        if 'ignoreDifferences' in app_def:
            app_manifest['spec']['ignoreDifferences'] = app_def['ignoreDifferences']

        # Transform to Python Inputs (snake_case)
        app_args = recursive_transform(app_manifest)


        # Create Resource
        # Resource name in Pulumi state must be unique
        resource_name = f"{cluster_name}-{app_name}"
        
        Application(
            resource_name,
            **app_args,
            opts=pulumi.ResourceOptions(provider=k8s_provider, protect=False) 
        )

# Design Note on Type Usage:
# This program generates Argo CD 'Application' custom resources from declarative YAML configurations.
# While 'crd2pulumi' generates strongly-typed Python classes (e.g., Application, ApplicationSpecArgs),
# we opt for a flexible dictionary-based approach combined with 'recursive_transform' for the following reasons:
#
# 1. Flexibility with Configuration: Our 'apps.yaml' and 'clusters/*.yaml' define applications
#    dynamically. Constructing Python objects from these arbitrary dictionaries would require
#    extensive, verbose, and error-prone manual mapping code for every nested field (spec, source,
#    destination, syncPolicy, etc.). The dictionary-based approach allows direct translation.
#
# 2. Generator Pattern: This Pulumi program acts as a *generator* of Argo CD Applications. Its
#    primary function is to interpret high-level configuration and produce the corresponding
#    Application YAML. Using dictionaries simplifies this "template engine" role.
#
# 3. Custom App Development: Strongly-typed CRD classes are highly beneficial when developing a
#    custom Pulumi program to define a *specific* application from scratch (e.g., writing Python
#    code to create a custom database deployment). In such cases, direct instantiation (e.g.,
#    Application(spec=ApplicationSpecArgs(...))) offers full IDE support and compile-time validation.
#
# 4. Runtime Validation: By unpacking the transformed dictionary (**app_args) into the Application
#    constructor, Pulumi's SDK still performs runtime validation against the generated schema. This
#    catches structural errors that might arise from misconfigurations in 'apps.yaml' or 'clusters/*.yaml'.
#
# In essence, this approach prioritizes configurability and brevity for a generic application
# generator, while still leveraging Pulumi's type-aware resource creation for validation.


# Main
clusters_files = ['clusters/mc.yaml', 'clusters/cc.yaml']

for cf in clusters_files:
    full_path = os.path.join(root_dir, cf)
    process_cluster(full_path)