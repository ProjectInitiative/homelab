{ pkgs, pythonEnv }:
pkgs.writeShellScriptBin "diff-manifests" ''
  set -e
  export PATH="${pythonEnv}/bin:${pkgs.nodejs_22}/bin:$PATH"
  PROJECT_ROOT=$(git rev-parse --show-toplevel)
  COMPARE_DIR="$PROJECT_ROOT/.direnv/compare"
  WORKTREE_DIR="$COMPARE_DIR/worktree"
  MANIFESTS_MAIN="$COMPARE_DIR/manifests-main"
  MANIFESTS_CURRENT="$COMPARE_DIR/manifests-current"

  cleanup() {
    if [ -d "$WORKTREE_DIR" ]; then
      git worktree remove --force "$WORKTREE_DIR" || true
    fi
  }
  trap cleanup EXIT

  rm -rf "$COMPARE_DIR"
  mkdir -p "$COMPARE_DIR"

  echo "Checking out 'main' branch to $WORKTREE_DIR..."
  git fetch origin main
  git worktree add --force --detach "$WORKTREE_DIR" origin/main

  # --- Generate MAIN manifests ---
  # If main has generator/ (post-merge), use cdk8s.
  # If main has pulumi/ (pre-merge), use the Pulumi generator with pyyaml-only fallback.
  echo "Generating manifests for MAIN..."
  mkdir -p "$MANIFESTS_MAIN"
  if [ -f "$WORKTREE_DIR/generator/main.py" ]; then
    (
      cd "$WORKTREE_DIR/generator"
      MANIFEST_OUTPUT_DIR="$MANIFESTS_MAIN" ${pythonEnv}/bin/python main.py
    )
  elif [ -f "$WORKTREE_DIR/pulumi/__main__.py" ]; then
    # Main still uses Pulumi. Extract the dict-building logic and run it
    # with the uv2nix python (pyyaml is available, Pulumi imports are not needed
    # because we write YAML directly).
    ${pythonEnv}/bin/python -c "
import yaml, json, os, sys, copy

sys.path.insert(0, '$WORKTREE_DIR')

def load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)

root_dir = '$WORKTREE_DIR'
apps_catalog = load_yaml(os.path.join(root_dir, 'apps.yaml'))
defaults = apps_catalog.get('defaults', {})
catalog = apps_catalog.get('catalog', {})

def apply_patch_to_source(src_obj, patch_content, patch_target=None):
    if 'kustomize' not in src_obj:
        src_obj['kustomize'] = {}
    patch_entry = {'patch': patch_content}
    if patch_target:
        patch_entry['target'] = patch_target
    if 'patches' not in src_obj['kustomize']:
        src_obj['kustomize']['patches'] = []
    src_obj['kustomize']['patches'].append(patch_entry)

def process_cluster(cluster_file):
    cluster_config = load_yaml(cluster_file)
    if not cluster_config:
        return
    cluster_name = cluster_config['name']
    server_url = cluster_config['server']
    argo_namespace = cluster_config['argoNamespace']
    vault_mount = cluster_config.get('vaultMount')
    for app_deployment in cluster_config.get('apps', []):
        app_name = app_deployment['name']
        app_def = catalog.get(app_name)
        if not app_def:
            continue
        target_ns = app_deployment.get('namespace')
        if not target_ns:
            continue
        sources = []
        if 'sources' in app_def:
            sources = copy.deepcopy(app_def['sources'])
        else:
            source = {
                'repoURL': app_def.get('repoURL', defaults.get('repoURL')),
                'targetRevision': app_def.get('targetRevision', defaults.get('targetRevision')),
                'path': app_def.get('path'),
                'chart': app_def.get('chart')
            }
            if 'directory' in app_def:
                source['directory'] = app_def['directory']
            if 'plugin' in app_deployment:
                source['plugin'] = app_deployment['plugin']
            elif 'plugin' in app_def:
                source['plugin'] = app_def['plugin']
            source = {k: v for k, v in source.items() if v is not None}
            sources = [source]
        if 'patch' in app_deployment and app_deployment['patch']:
            legacy_target_source = sources[0]
            if 'patchSourceIndex' in app_deployment:
                idx = app_deployment['patchSourceIndex']
                if 0 <= idx < len(sources):
                    legacy_target_source = sources[idx]
            apply_patch_to_source(legacy_target_source, app_deployment['patch'], app_deployment.get('patchTarget'))
        if 'patches' in app_deployment and isinstance(app_deployment['patches'], list):
            for p in app_deployment['patches']:
                if 'patch' not in p:
                    continue
                patch_src_idx = p.get('sourceIndex', 0)
                if 0 <= patch_src_idx < len(sources):
                    apply_patch_to_source(sources[patch_src_idx], p['patch'], p.get('target'))
        target_source_for_helm_values = sources[0]
        for src in sources:
            if 'chart' in src and 'helm' in src:
                target_source_for_helm_values = src
                break
        if 'helm_values' in app_deployment or 'value_files' in app_deployment:
            if 'helm' not in target_source_for_helm_values:
                target_source_for_helm_values['helm'] = {}
            if 'helm_values' in app_deployment:
                target_source_for_helm_values['helm']['values'] = app_deployment['helm_values']
            if 'value_files' in app_deployment:
                existing = target_source_for_helm_values['helm'].get('valueFiles', [])
                if not isinstance(existing, list):
                    existing = [existing]
                new_files = app_deployment['value_files']
                if not isinstance(new_files, list):
                    new_files = [new_files]
                target_source_for_helm_values['helm']['valueFiles'] = existing + new_files
        if 'vaultSecrets' in app_def:
            vs_config = app_def['vaultSecrets']
            secrets_list = vs_config.get('secrets', [])
            default_auth_name = vs_config.get('auth', 'operator-auth')
            common_repo = {'repoURL': 'https://github.com/projectinitiative/homelab.git', 'targetRevision': 'HEAD'}
            if vs_config.get('createAuth', False) and vault_mount:
                vault_role = vs_config.get('role', 'openbao-secrets-operator')
                generated_sa_name = f'{default_auth_name}-sa'
                audiences = vs_config.get('audiences', [])
                vault_auth_manifest = {
                    'apiVersion': 'secrets.hashicorp.com/v1beta1',
                    'kind': 'VaultAuth',
                    'metadata': {'name': 'placeholder-auth', 'namespace': target_ns},
                    'spec': {'method': 'kubernetes', 'mount': vault_mount,
                             'kubernetes': {'role': vault_role, 'serviceAccount': generated_sa_name}}
                }
                if 'namespace' in vs_config:
                    vault_auth_manifest['spec']['namespace'] = vs_config['namespace']
                if audiences:
                    vault_auth_manifest['spec']['kubernetes']['audiences'] = audiences
                va_patch_str = yaml.safe_dump(vault_auth_manifest)
                va_rename = json.dumps([{'op': 'replace', 'path': '/metadata/name', 'value': default_auth_name}])
                sa_rename = json.dumps([{'op': 'replace', 'path': '/metadata/name', 'value': generated_sa_name}])
                auth_source = common_repo.copy()
                auth_source['path'] = 'bootstrap/base/common/vault-resources/auth'
                apply_patch_to_source(auth_source, va_patch_str, {'kind': 'VaultAuth', 'name': 'placeholder-auth'})
                apply_patch_to_source(auth_source, va_rename, {'kind': 'VaultAuth', 'name': 'placeholder-auth'})
                apply_patch_to_source(auth_source, sa_rename, {'kind': 'ServiceAccount', 'name': 'placeholder-sa'})
                sources.append(auth_source)
            for secret_item in secrets_list:
                vss_manifest = {
                    'apiVersion': 'secrets.hashicorp.com/v1beta1',
                    'kind': 'VaultStaticSecret',
                    'metadata': {'name': 'placeholder-secret', 'namespace': target_ns},
                    'spec': {
                        'vaultAuthRef': secret_item.get('auth', default_auth_name),
                        'mount': secret_item.get('mount', 'secret'),
                        'type': secret_item.get('type', 'kv-v2'),
                        'path': secret_item['path'],
                        'destination': {'name': secret_item['destination'], 'create': True}
                    }
                }
                if 'refreshInterval' in secret_item:
                    vss_manifest['spec']['refreshInterval'] = secret_item['refreshInterval']
                if 'namespace' in vs_config:
                    vss_manifest['spec']['namespace'] = vs_config['namespace']
                vss_patch_str = yaml.safe_dump(vss_manifest)
                vss_rename = json.dumps([{'op': 'replace', 'path': '/metadata/name', 'value': secret_item['name']}])
                secret_source = common_repo.copy()
                secret_source['path'] = 'bootstrap/base/common/vault-resources/secret'
                apply_patch_to_source(secret_source, vss_patch_str, {'kind': 'VaultStaticSecret', 'name': 'placeholder-secret'})
                apply_patch_to_source(secret_source, vss_rename, {'kind': 'VaultStaticSecret', 'name': 'placeholder-secret'})
                sources.append(secret_source)
        if app_def.get('critical', False):
            if sources:
                primary_src = sources[0]
                if 'plugin' not in primary_src:
                    primary_src['plugin'] = {}
                if 'env' not in primary_src['plugin']:
                    primary_src['plugin']['env'] = []
                primary_src['plugin']['env'].append({'name': 'ADD_PROTECTED_LABEL', 'value': 'true'})
            pdb_source = {'repoURL': 'https://github.com/projectinitiative/homelab.git', 'targetRevision': 'HEAD', 'path': 'bootstrap/base/common/pdb'}
            pdb_rename = json.dumps([{'op': 'replace', 'path': '/metadata/name', 'value': f'{app_name}-pdb'}])
            apply_patch_to_source(pdb_source, pdb_rename, {'kind': 'PodDisruptionBudget', 'name': 'critical-pdb-placeholder'})
            sources.append(pdb_source)
        destination = {'server': server_url, 'namespace': target_ns}
        default_automated = {'prune': True, 'selfHeal': True}
        default_sync_options = ['CreateNamespace=true']
        app_sync_policy = app_def.get('syncPolicy', {})
        final_automated = app_sync_policy.get('automated', default_automated)
        final_sync_options = app_sync_policy.get('syncOptions', default_sync_options)
        sync_policy = {}
        if final_automated:
            sync_policy['automated'] = final_automated
        if final_sync_options is not None and final_sync_options:
            sync_policy['syncOptions'] = final_sync_options
        if 'vaultSecrets' in app_def:
            sync_policy['managedNamespaceMetadata'] = {'labels': {'vault-auth': 'enabled'}}
        app_manifest = {
            'apiVersion': 'argoproj.io/v1alpha1',
            'kind': 'Application',
            'metadata': {'name': app_name, 'namespace': argo_namespace,
                         'finalizers': ['resources-finalizer.argocd.argoproj.io']},
            'spec': {'project': cluster_config.get('project', 'default'), 'sources': sources,
                     'destination': destination, 'syncPolicy': sync_policy}
        }
        if 'annotations' in app_def:
            app_manifest['metadata']['annotations'] = app_def['annotations']
        if 'ignoreDifferences' in app_def:
            app_manifest['spec']['ignoreDifferences'] = app_def['ignoreDifferences']
        file_path = os.path.join('$MANIFESTS_MAIN', f'{cluster_name}-{app_name}.yaml')
        with open(file_path, 'w') as f:
            yaml.safe_dump(app_manifest, f, default_flow_style=False, sort_keys=False)

for cf in ['clusters/mc.yaml', 'clusters/cc.yaml']:
    full_path = os.path.join(root_dir, cf)
    if os.path.exists(full_path):
        process_cluster(full_path)
print('Generated baselines from main branch', file=sys.stderr)
"
  else
    echo "Error: neither generator/main.py nor pulumi/__main__.py found in main branch"
    exit 1
  fi

  # --- Generate CURRENT manifests ---
  echo "Generating manifests for CURRENT..."
  mkdir -p "$MANIFESTS_CURRENT"
  (
    cd "$PROJECT_ROOT/generator"
    MANIFEST_OUTPUT_DIR="$MANIFESTS_CURRENT" ${pythonEnv}/bin/python main.py
  )

  # --- Diff ---
  echo "Diffing manifests..."
  ${pkgs.dyff}/bin/dyff between -b --ignore-order-changes \
    "$MANIFESTS_MAIN/" "$MANIFESTS_CURRENT/" || true
  echo "Diff complete."
''
