{ pkgs, config, lib, ... }:

let
  # uv2nix-built virtualenv from generator/uv.lock
  generatorEnv = config.languages.python.import ./generator { };

  # Nix-built scripts using the uv2nix pythonEnv (shared with nix run .#*)
  generate-manifests = pkgs.writeShellScriptBin "generate-manifests" ''
    set -e
    export PATH="${generatorEnv}/bin:${pkgs.nodejs_22}/bin:$PATH"
    export MANIFEST_OUTPUT_DIR="''${MANIFEST_OUTPUT_DIR:-$PWD/.direnv/manifests}"
    mkdir -p "$MANIFEST_OUTPUT_DIR"
    cd "$PWD/generator"
    ${generatorEnv}/bin/python main.py
  '';

  diff-manifests = pkgs.writeShellScriptBin "diff-manifests" ''
    set -e
    export PATH="${generatorEnv}/bin:${pkgs.nodejs_22}/bin:$PATH"
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

    echo "Generating manifests for MAIN..."
    mkdir -p "$MANIFESTS_MAIN"
    if [ -f "$WORKTREE_DIR/generator/main.py" ]; then
      (
        cd "$WORKTREE_DIR/generator"
        MANIFEST_OUTPUT_DIR="$MANIFESTS_MAIN" ${generatorEnv}/bin/python main.py
      )
    elif [ -f "$WORKTREE_DIR/pulumi/__main__.py" ]; then
      ${generatorEnv}/bin/python -c "
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
    if 'kustomize' not in src_obj: src_obj['kustomize'] = {}
    patch_entry = {'patch': patch_content}
    if patch_target: patch_entry['target'] = patch_target
    if 'patches' not in src_obj['kustomize']: src_obj['kustomize']['patches'] = []
    src_obj['kustomize']['patches'].append(patch_entry)
def process_cluster(cluster_file):
    cluster_config = load_yaml(cluster_file)
    if not cluster_config: return
    cluster_name = cluster_config['name']
    server_url = cluster_config['server']
    argo_namespace = cluster_config['argoNamespace']
    vault_mount = cluster_config.get('vaultMount')
    for app_deployment in cluster_config.get('apps', []):
        app_name = app_deployment['name']
        app_def = catalog.get(app_name)
        if not app_def: continue
        target_ns = app_deployment.get('namespace')
        if not target_ns: continue
        sources = []
        if 'sources' in app_def: sources = copy.deepcopy(app_def['sources'])
        else:
            source = {'repoURL': app_def.get('repoURL', defaults.get('repoURL')), 'targetRevision': app_def.get('targetRevision', defaults.get('targetRevision')), 'path': app_def.get('path'), 'chart': app_def.get('chart')}
            if 'directory' in app_def: source['directory'] = app_def['directory']
            if 'plugin' in app_deployment: source['plugin'] = app_deployment['plugin']
            elif 'plugin' in app_def: source['plugin'] = app_def['plugin']
            source = {k: v for k, v in source.items() if v is not None}
            sources = [source]
        if 'patch' in app_deployment and app_deployment['patch']:
            legacy = sources[0]
            if 'patchSourceIndex' in app_deployment:
                idx = app_deployment['patchSourceIndex']
                if 0 <= idx < len(sources): legacy = sources[idx]
            apply_patch_to_source(legacy, app_deployment['patch'], app_deployment.get('patchTarget'))
        if 'patches' in app_deployment and isinstance(app_deployment['patches'], list):
            for p in app_deployment['patches']:
                if 'patch' not in p: continue
                idx = p.get('sourceIndex', 0)
                if 0 <= idx < len(sources): apply_patch_to_source(sources[idx], p['patch'], p.get('target'))
        target_helm = sources[0]
        for src in sources:
            if 'chart' in src and 'helm' in src: target_helm = src; break
        if 'helm_values' in app_deployment or 'value_files' in app_deployment:
            if 'helm' not in target_helm: target_helm['helm'] = {}
            if 'helm_values' in app_deployment: target_helm['helm']['values'] = app_deployment['helm_values']
            if 'value_files' in app_deployment:
                existing = target_helm['helm'].get('valueFiles', [])
                if not isinstance(existing, list): existing = [existing]
                new = app_deployment['value_files']
                if not isinstance(new, list): new = [new]
                target_helm['helm']['valueFiles'] = existing + new
        if 'vaultSecrets' in app_def:
            vs = app_def['vaultSecrets']
            default_auth = vs.get('auth', 'operator-auth')
            common = {'repoURL': 'https://github.com/projectinitiative/homelab.git', 'targetRevision': 'HEAD'}
            if vs.get('createAuth', False) and vault_mount:
                sa_name = f'{default_auth}-sa'
                va = {'apiVersion': 'secrets.hashicorp.com/v1beta1', 'kind': 'VaultAuth', 'metadata': {'name': 'placeholder-auth', 'namespace': target_ns}, 'spec': {'method': 'kubernetes', 'mount': vault_mount, 'kubernetes': {'role': vs.get('role', 'openbao-secrets-operator'), 'serviceAccount': sa_name}}}
                if 'namespace' in vs: va['spec']['namespace'] = vs['namespace']
                if vs.get('audiences'): va['spec']['kubernetes']['audiences'] = vs['audiences']
                va_str = yaml.safe_dump(va)
                va_rename = json.dumps([{'op': 'replace', 'path': '/metadata/name', 'value': default_auth}])
                sa_rename = json.dumps([{'op': 'replace', 'path': '/metadata/name', 'value': sa_name}])
                auth_src = common.copy(); auth_src['path'] = 'bootstrap/base/common/vault-resources/auth'
                apply_patch_to_source(auth_src, va_str, {'kind': 'VaultAuth', 'name': 'placeholder-auth'})
                apply_patch_to_source(auth_src, va_rename, {'kind': 'VaultAuth', 'name': 'placeholder-auth'})
                apply_patch_to_source(auth_src, sa_rename, {'kind': 'ServiceAccount', 'name': 'placeholder-sa'})
                sources.append(auth_src)
            for s in vs.get('secrets', []):
                vss = {'apiVersion': 'secrets.hashicorp.com/v1beta1', 'kind': 'VaultStaticSecret', 'metadata': {'name': 'placeholder-secret', 'namespace': target_ns}, 'spec': {'vaultAuthRef': s.get('auth', default_auth), 'mount': s.get('mount', 'secret'), 'type': s.get('type', 'kv-v2'), 'path': s['path'], 'destination': {'name': s['destination'], 'create': True}}}
                if 'refreshInterval' in s: vss['spec']['refreshInterval'] = s['refreshInterval']
                if 'namespace' in vs: vss['spec']['namespace'] = vs['namespace']
                vss_str = yaml.safe_dump(vss)
                vss_rename = json.dumps([{'op': 'replace', 'path': '/metadata/name', 'value': s['name']}])
                sec_src = common.copy(); sec_src['path'] = 'bootstrap/base/common/vault-resources/secret'
                apply_patch_to_source(sec_src, vss_str, {'kind': 'VaultStaticSecret', 'name': 'placeholder-secret'})
                apply_patch_to_source(sec_src, vss_rename, {'kind': 'VaultStaticSecret', 'name': 'placeholder-secret'})
                sources.append(sec_src)
        if app_def.get('critical', False):
            if sources:
                p = sources[0]
                if 'plugin' not in p: p['plugin'] = {}
                if 'env' not in p['plugin']: p['plugin']['env'] = []
                p['plugin']['env'].append({'name': 'ADD_PROTECTED_LABEL', 'value': 'true'})
            pdb_src = {'repoURL': 'https://github.com/projectinitiative/homelab.git', 'targetRevision': 'HEAD', 'path': 'bootstrap/base/common/pdb'}
            pdb_rename = json.dumps([{'op': 'replace', 'path': '/metadata/name', 'value': f'{app_name}-pdb'}])
            apply_patch_to_source(pdb_src, pdb_rename, {'kind': 'PodDisruptionBudget', 'name': 'critical-pdb-placeholder'})
            sources.append(pdb_src)
        sync_policy = {}
        auto = app_def.get('syncPolicy', {}).get('automated', {'prune': True, 'selfHeal': True})
        opts = app_def.get('syncPolicy', {}).get('syncOptions', ['CreateNamespace=true'])
        if auto: sync_policy['automated'] = auto
        if opts: sync_policy['syncOptions'] = opts
        if 'vaultSecrets' in app_def: sync_policy['managedNamespaceMetadata'] = {'labels': {'vault-auth': 'enabled'}}
        manifest = {'apiVersion': 'argoproj.io/v1alpha1', 'kind': 'Application', 'metadata': {'name': app_name, 'namespace': argo_namespace, 'finalizers': ['resources-finalizer.argocd.argoproj.io']}, 'spec': {'project': cluster_config.get('project', 'default'), 'sources': sources, 'destination': {'server': server_url, 'namespace': target_ns}, 'syncPolicy': sync_policy}}
        if 'annotations' in app_def: manifest['metadata']['annotations'] = app_def['annotations']
        if 'ignoreDifferences' in app_def: manifest['spec']['ignoreDifferences'] = app_def['ignoreDifferences']
        with open(os.path.join('$MANIFESTS_MAIN', f'{cluster_name}-{app_name}.yaml'), 'w') as f:
            yaml.safe_dump(manifest, f, default_flow_style=False, sort_keys=False)
for cf in ['clusters/mc.yaml', 'clusters/cc.yaml']:
    fp = os.path.join(root_dir, cf)
    if os.path.exists(fp): process_cluster(fp)
print('Generated baselines from main', file=sys.stderr)
"
    else
      echo "Error: neither generator/main.py nor pulumi/__main__.py found in main"
      exit 1
    fi

    echo "Generating manifests for CURRENT..."
    mkdir -p "$MANIFESTS_CURRENT"
    (
      cd "$PROJECT_ROOT/generator"
      MANIFEST_OUTPUT_DIR="$MANIFESTS_CURRENT" ${generatorEnv}/bin/python main.py
    )

    echo "Diffing manifests..."
    ${pkgs.dyff}/bin/dyff between -b --ignore-order-changes \
      "$MANIFESTS_MAIN/" "$MANIFESTS_CURRENT/" || true
    echo "Diff complete."
  '';
in
{
  cachix.enable = false;

  languages.python = {
    enable = true;
    uv.enable = true;
  };

  packages = [
    pkgs.nodejs_22
    pkgs.cdk8s-cli
    pkgs.dyff
    generatorEnv
    generate-manifests
    diff-manifests
  ];

  scripts.import-crds.exec = ''
    cd generator
    ${pkgs.cdk8s-cli}/bin/cdk8s import
  '';

  enterShell = ''
    echo "╔═══════════════════════════════════════════════╗"
    echo "║     Homelab cdk8s Development Shell           ║"
    echo "╚═══════════════════════════════════════════════╝"
    echo ""
    echo "Available commands:"
    echo "  generate-manifests  - Generate Argo CD Application manifests"
    echo "  diff-manifests      - Diff generated manifests against main"
    echo "  import-crds         - Import CRDs for cdk8s"
    echo ""
  '';

  enterTest = ''
    ${generatorEnv}/bin/python -c "from cdk8s import App; print('cdk8s OK')"
    ${generatorEnv}/bin/python -c "import yaml; print('pyyaml OK')"
  '';
}
