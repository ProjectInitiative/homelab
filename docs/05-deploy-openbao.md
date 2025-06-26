# Phase 4: Deploy OpenBao

With `step-ca` running, we can now deploy OpenBao and have `cert-manager` automatically issue it a TLS certificate.

## Steps

1.  **Create OpenBao Application:**
    Create an Argo CD application for OpenBao. This will be similar to your other application files.

2.  **Create OpenBao Certificate:**
    Create a `Certificate` resource for OpenBao. This will tell `cert-manager` to issue a certificate for OpenBao from your `step-ca` cluster issuer.

    ```yaml
    # In bootstrap/base/certs/openbao-certificate.yaml
    apiVersion: cert-manager.io/v1
    kind: Certificate
    metadata:
      name: openbao-server-tls
      namespace: openbao
    spec:
      secretName: openbao-server-tls
      issuerRef:
        name: step-ca-cluster-issuer
        kind: ClusterIssuer
      dnsNames:
        - openbao.openbao.svc.cluster.local
    ```

3.  **Commit and Push to Git:**
    Commit the new files to your Git repository. Argo CD will deploy OpenBao and `cert-manager` will issue the certificate.
