# Phase 3: Deploy step-ca via GitOps

Now that the database is ready and the root of trust secrets are in the cluster, we can update our GitOps repository to deploy `step-ca`.

## Steps

1.  **Update `step-ca-values.yaml`:**
    Modify `bootstrap/base/helm-values/step-ca-values.yaml` to use the PostgreSQL database and the secrets we created.

    ```yaml
    # In bootstrap/base/helm-values/step-ca-values.yaml
    replicaCount: 3

    existingSecrets:
      enabled: true
      ca: true
      issuer: true
      certsAsSecret: true
      configAsSecret: true

    bootstrap:
      enabled: false

    config:
      ca.json: |
        {
          "address": ":9000",
          "dnsNames": [
            "step-ca.step-ca.svc.cluster.local",
            "step-ca.step-ca.svc"
          ],
          "logger": {
            "format": "json"
          },
          "db": {
            "type": "postgres"
          },
          "authority": {},
          "tls": {
            "cipherSuites": [
              "TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384",
              "TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256"
            ],
            "minVersion": "1.2"
          },
          "acme": {
            "enabled": true
          }
        }
    env:
      - name: STEP_DB_DATASOURCE
        valueFrom:
          secretKeyRef:
            name: step-ca-db-datasource
            key: datasource
    ```

    **Note:** The `dataSource` is now pulled from the `step-ca-db-datasource` secret, ensuring the password is not committed to Git.

2.  **Commit and Push to Git:**
    Commit the changes to your Git repository. Argo CD will detect the changes and deploy `step-ca`.

    ```bash
    git add bootstrap/base/helm-values/step-ca-values.yaml
    git commit -m "Configure step-ca for HA with PostgreSQL"
    git push
    ```
