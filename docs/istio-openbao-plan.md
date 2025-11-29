# Plan: Istio Multi-Cluster with OpenBao for CA and Secrets

This document outlines the plan to set up a multi-primary Istio service mesh across two clusters, using OpenBao for two distinct purposes:
1.  **As a Root Certificate Authority (CA):** To sign the intermediate CA certificates for each cluster's Istio control plane.
2.  **As a Secrets Store:** To store the `remote-secret` required for cross-cluster endpoint discovery, and sync it to the clusters using the Vault Secrets Operator.

## Phased Approach

We will implement this in two phases to manage complexity.

### Phase 1: Istio CA Setup (Completed)

This phase involved configuring OpenBao as a root CA and setting up `cert-manager` in each cluster to request intermediate CA certificates. This part of the setup is complete.

### Phase 2: Istio Installation and Secrets Management

This phase involves installing Istio itself and using OpenBao to manage the `remote-secret` for endpoint discovery.

#### **Step 1: Install the Vault Secrets Operator**

*   **Action:** Create ArgoCD `Application` manifests to deploy the Vault Secrets Operator in both Cluster A and Cluster B.
*   **Details:** The operator will be configured to authenticate with OpenBao using the Kubernetes auth method we've already set up.

#### **Step 2: Configure OpenBao for the Vault Secrets Operator**

*   **Action:** Update the OpenBao configuration to grant the Vault Secrets Operator the necessary permissions to read secrets from the KV store.
*   **Details:** This involves creating a new policy in OpenBao and updating the Kubernetes auth roles for the operator's service accounts.

*   **Commands:**

    1.  **Create the policy in OpenBao:** This policy will allow the operator to read secrets from the `kv/istio/remote-secrets/` path.

        ```bash
        bao policy write -namespace=production vault-secrets-operator - <<EOF
        path "kv/data/istio/remote-secrets/*" {
          capabilities = ["read"]
        }
        EOF
        ```

    2.  **Update the Kubernetes auth roles:** Add the `vault-secrets-operator` policy to the roles for the operator's service account in both clusters. The operator runs in the `vault-secrets-operator` namespace by default.

        ```bash
        # For Cluster A
        bao write auth/kubernetes_cluster_a/role/vault-secrets-operator \
            bound_service_account_names=vault-secrets-operator \
            bound_service_account_namespaces=vault-secrets-operator \
            policies="vault-secrets-operator" \
            ttl=24h

        # For Cluster B
        bao write auth/kubernetes_cluster_b/role/vault-secrets-operator \
            bound_service_account_names=vault-secrets-operator \
            bound_service_account_namespaces=vault-secrets-operator \
            policies="vault-secrets-operator" \
            ttl=24h
        ```

#### **Step 3: Generate and Store the Istio Remote Secret**

*   **Action:** Manually generate the `remote-secret` for each cluster and store it in OpenBao's KV store.
*   **Details:** This is a one-time manual step. We will use `istioctl create-remote-secret --dry-run` to generate the secret manifest, extract the relevant data, and write it to a specific path in OpenBao (e.g., `kv/istio/remote-secrets/cluster-a`).

*   **Commands:**

    You will need to run these commands from a machine with `kubectl` access to both clusters and the `istioctl` CLI installed.

    1.  **Generate and store the secret for Cluster A:**

        ```bash
        # Generate the secret for Cluster A, which will be used by Cluster B
        REMOTE_SECRET_A=$(istioctl create-remote-secret --context="${CTX_CLUSTER1}" --name=cluster-a --dry-run)

        # Extract the secret data and write it to OpenBao
        echo "$REMOTE_SECRET_A" | yq -r '.data' | bao kv put -namespace=production kv/istio/remote-secrets/cluster-a -
        ```

    2.  **Generate and store the secret for Cluster B:**

        ```bash
        # Generate the secret for Cluster B, which will be used by Cluster A
        REMOTE_SECRET_B=$(istioctl create-remote-secret --context="${CTX_CLUSTER2}" --name=cluster-b --dry-run)

        # Extract the secret data and write it to OpenBao
        echo "$REMOTE_SECRET_B" | yq -r '.data' | bao kv put -namespace=production kv/istio/remote-secrets/cluster-b -
        ```
    
    **Note:** You will need the `yq` utility to run these commands. If you don't have it, you can install it from [here](https://github.com/mikefarah/yq). Alternatively, you can manually parse the YAML output of the `istioctl` command.

#### **Step 4: Create `VaultSecret` Custom Resources**

*   **Action:** Create `VaultSecret` custom resources in each cluster.
*   **Details:** This resource tells the Vault Secrets Operator which secret to fetch from OpenBao and where to create the corresponding Kubernetes `Secret` object. For example, in Cluster B, we will create a `VaultSecret` that points to `kv/istio/remote-secrets/cluster-a` and creates the `istio-remote-secret-cluster-a` Kubernetes `Secret`.

#### **Step 5: Install Istio**

*   **Action:** Create ArgoCD `Application` manifests to deploy Istio (`istio-base` and `istiod`) in both clusters.
*   **Details:** The Istio installation will be configured to use the `cacerts` secret (from Phase 1) and the `remote-secret` (from the previous steps).

This plan will result in a fully automated, GitOps-managed Istio multi-cluster setup where both the CA and the endpoint discovery secrets are managed by OpenBao.
