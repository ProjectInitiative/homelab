# Phase 5: Connect OpenBao to Argo CD

This final phase completes the GitOps loop by migrating the PostgreSQL secret to OpenBao and configuring Argo CD to use it.

## Steps

1.  **Store the PostgreSQL Secret in OpenBao:**
    Once OpenBao is running, store the PostgreSQL credentials in its key-value store.

2.  **Configure Argo CD Vault Plugin:**
    Install and configure the Argo CD Vault Plugin. This will allow Argo CD to retrieve secrets from OpenBao.

3.  **Update the `step-ca` Application:**
    Modify the `step-ca` Argo CD application to use the Vault plugin and retrieve the database credentials from OpenBao.

    ```yaml
    # In bootstrap/base/step-ca-app.yaml
    apiVersion: argoproj.io/v1alpha1
    kind: Application
    metadata:
      name: step-ca
      namespace: argocd
    spec:
      # ... other spec fields
      source:
        # ... other source fields
        helm:
          # ... other helm fields
          values: |
            config:
              ca.json: |
                {
                  "db": {
                    "type": "postgres",
                    "dataSource": "postgres://<path:kv/data/step-ca#username>:<path:kv/data/step-ca#password>@main-postgres-cluster.postgres.svc.cluster.local:5432/stepca?sslmode=disable"
                  }
                }
    ```

4.  **Delete the Temporary Secret:**
    Once Argo CD is successfully using the secret from OpenBao, you can delete the temporary Kubernetes secret.

    ```bash
    kubectl delete secret step-ca-db-creds -n step-ca
    ```

## Kubernetes Authentication for Vault Secrets Operator

The Vault Secrets Operator needs to authenticate with OpenBao to fetch secrets. This is done using OpenBao's Kubernetes authentication method.

### 1. Configure OpenBao (Policy and Role)

You need to create a Policy in OpenBao that grants read access to the secrets the operator needs, and a Role that binds this policy to the Kubernetes Service Account used by the operator.

**a. Create the Policy:**

This policy grants read access to the `k8s/data/tailscale-operator` path.

```bash
# Create a policy file named 'vso-policy.hcl'
cat <<EOF > vso-policy.hcl
path "k8s/data/tailscale-operator" {
  capabilities = ["read"]
}
EOF

# Apply the policy in OpenBao
# (Remember to set your BAO_NAMESPACE="production")
bao policy write vault-secrets-operator vso-policy.hcl
```

**b. Create the Role:**

This Role connects the Kubernetes Service Account (`operator` in namespace `openbao-secrets-operator`) to the `vault-secrets-operator` policy.

```bash
# Create the role, binding it to the service account, namespace, and policy
# (Remember to set your BAO_NAMESPACE="production")
bao write auth/kubernetes_cluster_mc/role/openbao-secrets-operator \
    bound_service_account_names=operator \
    bound_service_account_namespaces=openbao-secrets-operator \
    policies=vault-secrets-operator \
    ttl=24h
```

### 2. Create the Kubernetes `VaultAuth` Resource

The `VaultAuth` resource in Kubernetes tells the Vault Secrets Operator how to authenticate with OpenBao. It specifies the authentication method, mount path, and role to use.

```yaml
# In bootstrap/base/openbao-secrets-operator/vault-auth.yaml
apiVersion: secrets.hashicorp.com/v1beta1
kind: VaultAuth
metadata:
  name: operator-auth
  namespace: openbao-secrets-operator # Deployed in the operator's namespace
spec:
  method: kubernetes
  mount: kubernetes_cluster_mc # Matches the mount path in OpenBao
  kubernetes:
    role: openbao-secrets-operator # Matches the role created in OpenBao
    serviceAccount: operator # The service account used by the Vault Secrets Operator deployment
```

### 3. Update the Kubernetes `VaultStaticSecret` Resource

Finally, update your `VaultStaticSecret` to explicitly reference the `VaultAuth` resource you just created.

```yaml
# In bootstrap/base/tailscale-operator/openbao-secret.yaml
apiVersion: secrets.hashicorp.com/v1beta1
kind: VaultStaticSecret
metadata:
  name: tailscale-operator-oauth
  namespace: tailscale
spec:
  # ... other spec fields
  vaultAuthRef: openbao-secrets-operator/operator-auth # Reference the new VaultAuth resource
```

### Authentication Flow Summary

1.  The Vault Secrets Operator pod starts with its `operator` Service Account.
2.  It reads the `VaultAuth` resource, learning to use the `kubernetes` method at `kubernetes_cluster_mc` with the `openbao-secrets-operator` role.
3.  It presents its Kubernetes Service Account token to OpenBao.
4.  OpenBao validates the token with the Kubernetes API and, finding a matching Role, grants the operator an OpenBao token with the `vault-secrets-operator` policy.
5.  The operator uses this OpenBao token to read the Tailscale secret from `k8s/data/tailscale-operator`.