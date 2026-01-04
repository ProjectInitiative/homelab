# Registering Main Cluster (mc) with Karmada

This guide documents how to register the **Main Cluster (mc)** as a member of the Karmada control plane running on the **Control Cluster (cc)**.

Since `mc` is behind a Tailscale Proxy in `noauth` mode, we use a dedicated ServiceAccount (`karmada-member`) and a long-lived token.

## Prerequisites

1.  The `karmada-member` application must be synced to `mc`.
2.  You must have admin access to `mc` (via your `kylepzak-admin` token or internal access).
3.  You must have the `karmadactl` CLI installed (or `kubectl-karmada`).

## Step 1: Generate the Member Token

Run this against the **Main Cluster (mc)** to get a long-lived token for Karmada.

```bash
# Verify SA exists
kubectl --context=mc -n kube-system get sa karmada-member

# Generate token (Non-expiring / 10 years)
kubectl --context=mc -n kube-system create token karmada-member --duration=87660h
```
*Copy this token.*

## Step 2: Create a Member Kubeconfig

Create a temporary file `member-mc.kubeconfig` with the following content.

**Replace `<TOKEN>` with the token from Step 1.**
**Note:** The server URL is the Tailscale HA IP of `mc`.

```yaml
apiVersion: v1
kind: Config
preferences: {}
current-context: mc-context
clusters:
- cluster:
    insecure-skip-tls-verify: true
    server: https://100.81.206.243:443
  name: mc-cluster
users:
- name: karmada-member
  user:
    token: <TOKEN>
contexts:
- context:
    cluster: mc-cluster
    user: karmada-member
  name: mc-context
```

## Step 3: Register with Karmada

Run the join command against the **Control Cluster (cc)** where Karmada is running.

```bash
# Register 'mc' into Karmada
karmadactl --kubeconfig=<PATH_TO_CC_KUBECONFIG> join mc \
  --cluster-kubeconfig=member-mc.kubeconfig
```

*Note: `<PATH_TO_CC_KUBECONFIG>` is your normal admin access to the Control Cluster.*

## Verification

Check the status of the clusters in Karmada:

```bash
karmadactl --kubeconfig=<PATH_TO_CC_KUBECONFIG> get clusters
```
You should see `mc` listed with status `Ready`.

```
