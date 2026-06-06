#!/usr/bin/env python3
import json
import base64
import yaml
import subprocess
import os
import requests
import sys

# Configure Vault address and token from environment
VAULT_ADDR = os.environ.get("VAULT_ADDR", "http://openbao.openbao:8200") # Default to internal cluster address
VAULT_TOKEN = os.environ.get("VAULT_TOKEN")

def get_secret(context, namespace, secret_name):
    """Retrieve a Kubernetes secret using kubectl."""
    try:
        cmd = [
            "kubectl", "--context", context, "-n", namespace,
            "get", "secret", secret_name, "-o", "json"
        ]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error retrieving secret {secret_name} from {context}/{namespace}: {e.stderr}", file=sys.stderr)
        return None

def write_vault_secret(path, data):
    """Write data to Vault using requests."""
    if not VAULT_TOKEN:
        print("Error: VAULT_TOKEN environment variable is not set.", file=sys.stderr)
        return False

    url = f"{VAULT_ADDR}/v1/{path}"
    headers = {"X-Vault-Token": VAULT_TOKEN}

    # Vault KV v2 requires wrapping data in "data" key
    payload = {"data": data}

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        print(f"Successfully wrote secret to {path}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error writing to Vault path {path}: {e}", file=sys.stderr)
        return False

def sync_submariner(context_cc):
    """Sync Submariner broker info from CC to Vault."""
    print("Syncing Submariner broker info...")

    # Try generic name first
    secret = get_secret(context_cc, "submariner-k8s-broker", "submariner-broker-secret")

    if not secret:
        # Try finding by label
        print("Could not find submariner-broker-secret. Trying to find by label app=submariner-k8s-broker...")
        cmd = [
            "kubectl", "--context", context_cc, "-n", "submariner-k8s-broker",
            "get", "secrets", "-l", "app=submariner-k8s-broker", "-o", "json"
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True)
            secrets = json.loads(res.stdout).get('items', [])
            if secrets:
                secret = secrets[0] # Pick first one
                print(f"Found secret: {secret['metadata']['name']}")
            else:
                print("No suitable secret found for Submariner broker info.")
                return
        except Exception as e:
            print(f"Error listing secrets: {e}", file=sys.stderr)
            return

    # Extract data
    data = {}
    for k, v in secret.get('data', {}).items():
        try:
            # Try to decode UTF-8 (text files like broker-info.subm usually contain text/json)
            decoded = base64.b64decode(v).decode('utf-8')
            data[k] = decoded
        except Exception:
             print(f"Warning: Could not decode {k} as UTF-8. Storing as is (base64 encoded)? No, skipping to avoid corruption.")
             # If it's binary, Vault KV can store it if we encode it, but VSO will put it back.
             # If VSO expects to write to K8s Secret 'data' (base64), we should provide base64?
             # No, VSO takes string from Vault and puts it in 'data' (encoding it).
             # So if we have binary data, we can't easily store it in Vault KV as string unless we base64 it again.
             # But then VSO will double-encode it unless we use 'stringData' behavior or similar.
             # Assuming Submariner broker info is text.
             pass

    if data:
        write_vault_secret("submariner/broker-info", data)

def sync_karmada(context_cc):
    """Sync Karmada admin config from CC to Vault."""
    print("Syncing Karmada admin config...")
    # Karmada admin config is in "karmada-kubeconfig" secret in "karmada-system" namespace.
    secret = get_secret(context_cc, "karmada-system", "karmada-kubeconfig")
    if not secret:
        print("Could not find karmada-kubeconfig secret.")
        return

    if 'kubeconfig' not in secret.get('data', {}):
        print("Secret does not contain 'kubeconfig' key.")
        return

    kubeconfig_b64 = secret['data']['kubeconfig']
    kubeconfig_str = base64.b64decode(kubeconfig_b64).decode('utf-8')
    kubeconfig = yaml.safe_load(kubeconfig_str)

    # Extract info (Assuming single cluster)
    cluster = kubeconfig['clusters'][0]['cluster']
    user = kubeconfig['users'][0]['user']

    server = cluster['server']
    # Note: server URL might be internal. If ArgoCD is external, this needs adjustment.

    ca_data = cluster.get('certificate-authority-data')
    client_cert = user.get('client-certificate-data')
    client_key = user.get('client-key-data')
    token = user.get('token')

    # Construct ArgoCD config
    config = {
        "tlsClientConfig": {
            "insecure": False
        }
    }

    if ca_data:
        config["tlsClientConfig"]["caData"] = ca_data

    if token:
        config["bearerToken"] = token
    elif client_cert and client_key:
        config["tlsClientConfig"]["certData"] = client_cert
        config["tlsClientConfig"]["keyData"] = client_key

    vault_data = {
        "name": "karmada",
        "server": server,
        "config": json.dumps(config)
    }

    write_vault_secret("karmada/config", vault_data)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Sync secrets to Vault")
    parser.add_argument("--context-cc", default="cc", help="Kubectl context for Control Cluster")
    args = parser.parse_args()

    sync_submariner(args.context_cc)
    sync_karmada(args.context_cc)
