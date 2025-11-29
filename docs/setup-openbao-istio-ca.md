# How to Configure OpenBao as the Root CA for Istio

This guide details the steps to configure OpenBao to act as a root Certificate Authority (CA) for your Istio service mesh. We will use the Kubernetes authentication method to allow `cert-manager` to request intermediate certificates from OpenBao.

## Prerequisites

- You have a running OpenBao cluster.
- You have `kubectl` access to the cluster where OpenBao is running.
- You have the OpenBao root token.

## Steps

1.  **Port-forward to the OpenBao service:**

    ```bash
    kubectl -n openbao port-forward svc/openbao 8200:8200 &
    ```

2.  **Set environment variables for the OpenBao CLI:**

    ```bash
    export BAO_ADDR='http://127.0.0.1:8200'
    # or 80 if exposed over another method:
    export BAO_ADDR='http://openbao-ts.taildeab2.ts.net'

    export BAO_TOKEN='your-root-token' # Replace with your OpenBao root token
    ```

3.  **Create the 'production' namespace in OpenBao:**

    ```bash
    bao namespace create production
    ```

4.  **Enable and configure the PKI secrets engine as a root CA in the 'production' namespace:**

    ```bash
    # Enable the pki secrets engine at the path 'pki_k8s'
    bao secrets enable -namespace=production -path=pki_k8s pki

    # Set the max lease TTL for the root CA to 10 years
    bao secrets tune -namespace=production -max-lease-ttl=87600h pki_k8s

    # Generate the root certificate
    bao write -namespace=production -field=certificate pki_k8s/root/generate/internal \
        common_name="homelab.io" \
        issuer_name="homelab-root-ca" \
        ttl=87600h > root-ca.crt

    # Configure the CRL and issuing certificate endpoints
    bao write -namespace=production pki_k8s/config/urls \
        issuing_certificates="$BAO_ADDR/v1/production/pki_k8s/ca" \
        crl_distribution_points="$BAO_ADDR/v1/production/pki_k8s/crl"
    ```

5.  **Create a role for signing intermediate CA certificates in the 'production' namespace:**

    This role will be used by `cert-manager` to request intermediate certificates for each Istio cluster.

    ```bash
    bao write -namespace=production pki_k8s/roles/istio-intermediate \
        allow_any_name=true \
        max_ttl="43800h" \
        key_type=ec \
        key_bits=256 \
        require_cn=false \
        ou="Istio" \
        allow_subdomains=true \
        allowed_domains="cluster.local" \
        allow_bare_domains=true \
        is_ca=true \
        max_path_length=0
    ```

6.  **Enable and configure Kubernetes authentication for Cluster A in the 'production' namespace:**

    This will be the auth method for the cluster where OpenBao is running.

    ```bash
    # Enable the kubernetes auth method for Cluster A
    bao auth enable -namespace=production -path=kubernetes_cluster_a kubernetes

    # Configure it with the Kubernetes service account JWT from Cluster A
    # This command assumes you are running it from a machine with a valid kubeconfig for Cluster A
    bao write -namespace=production auth/kubernetes_cluster_a/config \
        token_reviewer_jwt="$(kubectl create token default)" \
        kubernetes_host="$(kubectl config view --minify -o jsonpath='{.clusters[0].cluster.server}')" \
        kubernetes_ca_cert=@"$(kubectl config view --raw --minify -o jsonpath='{.clusters[0].cluster.certificate-authority-data}' | base64 --decode > ca.crt && echo ca.crt)"

    # Cleanup the temporary ca.crt file
    rm ca.crt
    ```

7.  **Enable and configure Kubernetes authentication for Cluster B in the 'production' namespace:**

    You will repeat the process for Cluster B, using a different path and the credentials from Cluster B.

    ```bash
    # Enable the kubernetes auth method for Cluster B
    bao auth enable -namespace=production -path=kubernetes_cluster_b kubernetes

    # Configure it with the Kubernetes service account JWT from Cluster B
    # This command assumes you are running it from a machine with a valid kubeconfig for Cluster B
    # Ensure your KUBECONFIG is pointing to Cluster B for these commands
    bao write -namespace=production auth/kubernetes_cluster_b/config \
        token_reviewer_jwt="$(kubectl create token default)" \
        kubernetes_host="$(kubectl config view --minify -o jsonpath='{.clusters[0].cluster.server}')" \
        kubernetes_ca_cert=@"$(kubectl config view --raw --minify -o jsonpath='{.clusters[0].cluster.certificate-authority-data}' | base64 --decode > ca.crt && echo ca.crt)"

    # Cleanup the temporary ca.crt file
    rm ca.crt
    ```

8.  **Create a policy and roles for `cert-manager` in both clusters:**

    The policy grants permission to sign certificates. It is created once in the `production` namespace. The roles bind this policy to the `cert-manager` service account in each cluster.

    ```bash
    # Create a policy that allows signing intermediate certificates
    bao policy write -namespace=production cert-manager-istio - <<EOF
    path "pki_k8s/sign/istio-intermediate" {
      capabilities = ["create", "update"]
    }
    EOF

    # Create a role for Cluster A's cert-manager service account
    bao write -namespace=production auth/kubernetes_cluster_a/role/cert-manager-istio \
        bound_service_account_names=cert-manager \
        bound_service_account_namespaces=istio-system,cert-manager \
        policies="cert-manager-istio" \
        ttl=24h

    # Create a role for Cluster B's cert-manager service account
    bao write -namespace=production auth/kubernetes_cluster_b/role/cert-manager-istio \
        bound_service_account_names=cert-manager \
        bound_service_account_namespaces=istio-system,cert-manager \
        policies="cert-manager-istio" \
        ttl=24h
    ```

After completing these steps, OpenBao is ready to issue intermediate certificates for your Istio clusters. The next step is to create a `ClusterIssuer` in Kubernetes that uses this configuration.

## Next Steps: Exposing OpenBao and Installing Istio

With OpenBao configured, the next phase is to expose it to your other cluster and then install Istio on both clusters, configuring them to use OpenBao as the CA.

### 1. Expose OpenBao to Cluster B

For Cluster B's `cert-manager` to communicate with OpenBao in Cluster A, you need to expose the OpenBao service over your private network. Since you are using Tailscale, you can use a `LoadBalancer` service with a Tailscale IP.

Here is an example manifest to expose OpenBao. You would apply this in **Cluster A**.

```yaml
# In bootstrap/base/openbao/openbao-tailscale-lb.yaml
apiVersion: v1
kind: Service
metadata:
  name: openbao-tailscale
  namespace: openbao
  annotations:
    tailscale.com/expose: "true"
    # You might want to assign a specific static IP from your Tailscale network
    # tailscale.com/hostname: "openbao"
spec:
  type: LoadBalancer
  selector:
    app.kubernetes.io/name: openbao
    component: server
  ports:
    - name: http
      port: 8200
      targetPort: 8200
```

Once applied, Tailscale will provision a load balancer and assign an IP address. You will use this IP address in the `baoIssuer` configuration for Cluster B.

### 2. Configure Istio on Each Cluster

You will now deploy the necessary `cert-manager` issuers and certificates to each cluster, and then install Istio.

#### **On Cluster A:**

1.  **Deploy the `baoIssuer` and `Certificate`:**
    Apply the `kustomization` in `bootstrap/base/istio/` to Cluster A. This will create the `baoIssuer` that connects to the local OpenBao and the `Certificate` resource that requests the intermediate CA for `cacerts`.

2.  **Wait for the `cacerts` secret:**
    Check that the secret is created successfully in the `istio-system` namespace:
    `kubectl -n istio-system get secret cacerts`

3.  **Install Istio:**
    Install Istio using an `IstioOperator` resource, ensuring it's configured for multi-cluster and points to the `cacerts` secret.

#### **On Cluster B:**

1.  **Create a `baoIssuer` for Cluster B:**
    You will need to create a `baoIssuer` in Cluster B that points to the Tailscale IP of the OpenBao service in Cluster A.

    ```yaml
    # In a new file for Cluster B's configuration
    apiVersion: cert-manager.io/v1
    kind: ClusterIssuer
    metadata:
      name: openbao-istio-ca
spec:
      bao:
        server: http://<TAILSCALE_IP_OF_OPENBAO>:8200
        path: production/pki_k8s/sign/istio-intermediate
        namespace: production
        auth:
          kubernetes:
            role: cert-manager-istio-cluster-b # Use the role created for Cluster B
            mountPath: /v1/auth/kubernetes_cluster_b # Use the auth path for Cluster B
            secretRef:
              name: cert-manager-bao-token
              key: token
    ```

2.  **Create a `Certificate` for Cluster B:**
    Create a `Certificate` resource in Cluster B to request its intermediate CA.

    ```yaml
    apiVersion: cert-manager.io/v1
    kind: Certificate
    metadata:
      name: istio-intermediate-ca-cluster-b
      namespace: istio-system
spec:
      isCA: true
      commonName: istio-intermediate-ca-cluster-b
      duration: 2160h # 90d
      renewBefore: 360h # 15d
      secretName: cacerts # Istio requires this specific name
      privateKey:
        algorithm: ECDSA
        size: 256
      issuerRef:
        name: openbao-istio-ca
        kind: ClusterIssuer
    ```

3.  **Wait for the `cacerts` secret and Install Istio:**
    Once the `cacerts` secret is created in Cluster B, you can install Istio there using an appropriate `IstioOperator` configuration for the second cluster.

### 3. Final Steps

1.  **Expose Control Planes:** Expose the Istio control planes (istiod) in each cluster to the other cluster, typically with an `East-West` gateway.
2.  **Enable Endpoint Discovery:** Configure Istio to discover endpoints in the other cluster.
3.  **Test:** Deploy a sample application across both clusters and verify that cross-cluster communication is working with mTLS.
