# Admin Access via Tailscale Proxy

This guide documents how to configure local `kubectl` access when using the Tailscale Kubernetes Operator's API Server Proxy in `noauth` mode.

## Context

We use the Tailscale API Server Proxy in `noauth` mode to allow automated systems (like OpenBao, Submariner, and CI/CD) to authenticate using ServiceAccount tokens. 

**Important:** `noauth` mode terminates TLS at the proxy, meaning **Client Certificates** (the default authentication method for `k3s` admin configs) **will not work**. The proxy drops the certificate before the request reaches the API server.

To maintain admin access, we use a dedicated ServiceAccount (`kylepzak-admin`) and a long-lived Bearer Token.

## Prerequisites

1.  The `admin-access` application must be synced in Argo CD.
2.  You must have temporary access to the cluster (via the original internal IP, SSH port-forwarding, or the emergency `admin.conf` on the node) to generate the initial token.

## Step 1: Generate the Token

Run the following command against the **internal** cluster endpoint (not the Tailscale proxy yet) to generate a token valid for 1 year (8760 hours).

```bash
# Verify the account exists
kubectl -n kube-system get sa kylepzak-admin

# Generate the token
kubectl -n kube-system create token kylepzak-admin --duration=8760h
```

*Copy the output token.*

## Step 2: Configure Kubeconfig

Update your local `kubeconfig` to use the Tailscale Proxy URL and the new token.

**Replace the variables below:**
*   `<CLUSTER_NAME>`: Your context name (e.g., `default`, `mc`, or `cc`).
*   `<TAILSCALE_URL>`: The https URL of your Tailscale Proxy (e.g., `https://control-cluster-proxy.taildeab2.ts.net`).
*   `<TOKEN>`: The token string you copied in Step 1.

```bash
# 1. Set the Cluster URL to the Tailscale Proxy
kubectl config set-cluster <CLUSTER_NAME> --server=<TAILSCALE_URL>

# 2. Clear the Certificate Authority (Trust Tailscale's public Let's Encrypt certs)
kubectl config set-cluster <CLUSTER_NAME> --certificate-authority-data=null
kubectl config set-cluster <CLUSTER_NAME> --certificate-authority=null

# 3. Configure the User to use the Token
kubectl config set-credentials <CLUSTER_NAME> --token=<TOKEN>

# 4. Clear old Client Certs to prevent confusion/warnings
kubectl config set-credentials <CLUSTER_NAME> --client-certificate-data=null
kubectl config set-credentials <CLUSTER_NAME> --client-key-data=null
```

## Verification

Test your access:

```bash
kubectl get nodes
```

You should see the node list. If you inspect the request (via `-v=9`), you will see it is now using the `Authorization: Bearer ...` header instead of mTLS.

## Token Renewal

When the token expires (after 1 year), you will receive `401 Unauthorized` errors. Simply repeat **Step 1** using emergency access (SSH/Port-forward) and update your config with the new token.
