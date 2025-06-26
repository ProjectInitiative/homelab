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
