import yaml
import os
import sys
import subprocess
from deepdiff import DeepDiff
from pprint import pprint

def load_yaml_stream(stream_content):
    """Loads a stream of YAML documents."""
    try:
        return list(yaml.safe_load_all(stream_content))
    except yaml.YAMLError as e:
        print(f"Error parsing YAML: {e}", file=sys.stderr)
        return []

def load_yaml_file(file_path):
    """Loads a single YAML file."""
    try:
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading file {file_path}: {e}", file=sys.stderr)
        return None

def run_kustomize(path):
    """Runs kustomize build on a path and returns the output as a list of dicts."""
    print(f"Running kustomize build {path}...", file=sys.stderr)
    try:
        result = subprocess.run(
            ["kustomize", "build", path],
            capture_output=True,
            text=True,
            check=True
        )
        return load_yaml_stream(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Kustomize failed: {e.stderr}", file=sys.stderr)
        return []

def normalize_app(app):
    """Normalizes an Application object for comparison."""
    if not app:
        return None
        
    # Remove fields that are expected to differ or are not relevant for equivalence
    # metadata.creationTimestamp
    # metadata.generation
    # metadata.uid
    # metadata.resourceVersion
    # status (we only care about spec)
    
    normalized = app.copy()
    if 'metadata' in normalized:
        for key in ['creationTimestamp', 'generation', 'uid', 'resourceVersion', 'managedFields', 'labels']:
            normalized['metadata'].pop(key, None)
        
        # We specifically want to ignore 'labels' in metadata generally 
        # unless they are critical, because Pulumi might add its own tracking labels.
        # Annotations are important for ArgoCD (sync-waves, etc), so we keep them.
        # Finalizers are also important for ArgoCD (cascade deletion), so we keep them.    
    if 'status' in normalized:
        del normalized['status']
        
    # Normalize empty fields. Kustomize might omit empty lists, Pulumi might include them.
    if 'spec' in normalized:
        spec = normalized['spec']
        
        # Normalize source -> sources (list of 1)
        if 'source' in spec:
            if 'sources' not in spec:
                spec['sources'] = [spec['source']]
            del spec['source']
            
        if 'sources' in spec:
            for source in spec['sources']:
                if 'kustomize' in source:
                    if 'patches' in source['kustomize']:
                        for patch_entry in source['kustomize']['patches']:
                            if 'patch' in patch_entry and isinstance(patch_entry['patch'], str):
                                # Parse and re-serialize the YAML patch to normalize whitespace/comments
                                try:
                                    patch_data = yaml.safe_load(patch_entry['patch'])
                                    patch_entry['patch'] = yaml.safe_dump(patch_data, default_flow_style=False)
                                except yaml.YAMLError:
                                    # If it's not valid YAML, leave it as is
                                    pass
                        if not source['kustomize']['patches']:
                            del source['kustomize']['patches']
                    if not source['kustomize']: # Empty kustomize dict
                        del source['kustomize']
                
                if 'helm' in source:
                    if 'valueFiles' in source['helm'] and not source['helm']['valueFiles']:
                        del source['helm']['valueFiles']
                    if 'values' in source['helm'] and not source['helm']['values']:
                        del source['helm']['values']
                    if not source['helm']:
                        del source['helm']

        # Handle ignoreDifferences. 
        # If one has it and other doesn't, that's a diff.
    
    return normalized

def get_key(app):
    return f"{app['metadata'].get('namespace', 'default')}/{app['metadata']['name']}"

def main():
    # 1. Load Old State (Kustomize)
    old_apps = {}
    
    # Main Cluster Overlay
    mc_docs = run_kustomize("overlays/main-cluster")
    for doc in mc_docs:
        if doc and doc.get('kind') == 'Application':
            key = get_key(doc)
            old_apps[key] = normalize_app(doc)

    # Control Cluster Overlay
    cc_docs = run_kustomize("overlays/control-cluster")
    for doc in cc_docs:
        if doc and doc.get('kind') == 'Application':
            key = get_key(doc)
            old_apps[key] = normalize_app(doc)

    print(f"Found {len(old_apps)} existing Applications via Kustomize.", file=sys.stderr)

    # 2. Load New State (Pulumi Generated)
    new_apps = {}
    manifest_dir = ".direnv/manifests/1-manifest"
    if not os.path.exists(manifest_dir):
        print(f"Error: Manifest directory {manifest_dir} does not exist. Run 'pulumi up' first.", file=sys.stderr)
        sys.exit(1)

    for filename in os.listdir(manifest_dir):
        if filename.endswith(".yaml"):
            path = os.path.join(manifest_dir, filename)
            doc = load_yaml_file(path)
            if doc and doc.get('kind') == 'Application':
                key = get_key(doc)
                new_apps[key] = normalize_app(doc)

    print(f"Found {len(new_apps)} generated Applications via Pulumi.", file=sys.stderr)

    # 3. Compare
    all_keys = set(old_apps.keys()) | set(new_apps.keys())
    
    errors = 0
    
    print("\n--- COMPARISON RESULTS ---\n")

    for key in sorted(all_keys):
        old_app = old_apps.get(key)
        new_app = new_apps.get(key)

        if old_app is None:
            print(f"[+] NEW: {key}")
            # This might be expected if we added LPP/Kube-vip which were previously skipped or part of bootstrap
            continue
            
        if new_app is None:
            print(f"[-] MISSING: {key}")
            errors += 1
            continue

        # Deep Diff
        diff = DeepDiff(old_app, new_app, ignore_order=True, report_repetition=True)
        if diff:
            print(f"[!] DIFF: {key}")
            pprint(diff)
            errors += 1
        else:
            print(f"[OK] {key}")

    if errors > 0:
        print(f"\nFAILURE: Found {errors} differences/missing apps.")
        sys.exit(1)
    else:
        print("\nSUCCESS: Configuration matches!")

if __name__ == "__main__":
    main()
