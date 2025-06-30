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

## Post-Deployment: Configure step-issuer

After `step-ca` is deployed and running, you'll need to configure `step-issuer` to communicate with it. This involves finding the `step-ca`'s provisioner name and KID, and providing its root CA certificate to `cert-manager`.

### 1. Find Provisioner Name and KID

The provisioner name and KID are part of your `step-ca`'s ACME configuration.

*   **Provisioner Name:** This is typically defined in your `step-ca`'s configuration file (e.g., `ca.json` if you're using the default setup). Look for the `acme` section and the `provisioners` array within it. The `name` field of an ACME provisioner entry is what you're looking for. If you haven't explicitly configured one, `step-ca` might create a default one.

*   **KID (Key ID):** The KID is a unique identifier for the public key associated with an ACME account. It's not a secret. You can find it by inspecting the `step-ca` logs or by querying the `step-ca` ACME directory.

    **To find the provisioner name and KID:**

    1.  **Get the `step-ca` pod name:**
        ```bash
        kubectl get pods -n step-ca -l app.kubernetes.io/name=step-ca -o jsonpath='{.items[0].metadata.name}'
        ```
        (Replace `step-ca` with your `step-ca` namespace if different).

    2.  **Inspect `step-ca` logs for provisioner details:**
        ```bash
        kubectl logs -n step-ca <step-ca-pod-name> | grep "provisioner"
        ```
        Look for log entries that mention "provisioner" and "kid".

    3.  **Alternatively, query the ACME directory (more advanced):**
        You can use `step cli` or a similar ACME client to query the ACME directory of your `step-ca` to list provisioners and their KIDs. This usually requires setting up `step cli` with your `step-ca` configuration.

### 2. Update `helm-values/step-issuer-values.yaml`

Once you have the provisioner name and KID, update `bootstrap/base/helm-values/step-issuer-values.yaml`:

```yaml
# In bootstrap/base/helm-values/step-issuer-values.yaml
stepClusterIssuer:
  create: true
  caUrl: "https://step-ca.step-ca.svc.cluster.local:443/acme/acme/directory"
  email: "no-reply@moonwake.io" # Your email for ACME registration
  caBundle:
    configMap:
      name: step-ca-ca-bundle
      key: ca.crt
  provisioner:
    name: "YOUR_PROVISIONER_NAME" # IMPORTANT: Replace with the actual provisioner name from step-ca
    kid: "YOUR_KID" # IMPORTANT: Replace with the actual KID from step-ca
    passwordRef:
      name: "step-issuer-provisioner-password" # Secret containing the provisioner password
      key: "password"
```

### 3. Create `step-ca-ca-bundle` ConfigMap

`cert-manager` needs to trust your `step-ca`'s root certificate. You'll create a `ConfigMap` containing the base64 encoded root CA certificate of your `step-ca`.

1.  **Get the `step-ca` root CA certificate:**
    You can usually find this in the `step-ca` pod's filesystem (e.g., `/home/step/certs/root_ca.crt` or similar, depending on your `step-ca` setup). You might need to `kubectl exec` into the `step-ca` pod to retrieve it.

    ```bash
    kubectl exec -it <step-ca-pod-name> -n step-ca -- cat /home/step/certs/root_ca.crt > root_ca.crt
    ```
    (Adjust the path to `root_ca.crt` if necessary based on your `step-ca` configuration).

2.  **Create the ConfigMap:**
    ```yaml
    apiVersion: v1
    kind: ConfigMap
    metadata:
      name: step-ca-ca-bundle
      namespace: cert-manager # Or the namespace where cert-manager is installed
    data:
      ca.crt: |
        -----BEGIN CERTIFICATE-----
        <PASTE_BASE64_ENCODED_ROOT_CA_CERT_HERE>
        -----END CERTIFICATE-----
    ```
    Replace `<PASTE_BASE64_ENCODED_ROOT_CA_CERT_HERE>` with the content of the `root_ca.crt` file you retrieved.

    Apply this ConfigMap to your cluster:
    ```bash
    kubectl apply -f your-configmap-file.yaml
    ```

### 4. Commit and Push to Git

Commit the changes to `bootstrap/base/helm-values/step-issuer-values.yaml` and push to your Git repository. Argo CD will then deploy `step-issuer` with the correct `ClusterIssuer` configuration.

```bash
git add bootstrap/base/helm-values/step-issuer-values.yaml
git commit -m "Configure step-issuer with step-ca provisioner details and caBundle reference"
git push
```