# Phase 2: The Root of Trust (Manual Bootstrap)

This is the most critical phase for the security and recoverability of your PKI. We will generate the CA keys and passwords locally and then create the necessary Kubernetes secrets manually. This ensures the root of trust is never stored in plaintext in Git and can be recovered in a disaster.

## Steps

1.  **Generate Passwords:**
    Generate strong, random passwords for the root key and the intermediate key. Store these securely in a password manager.

    ```bash
    # Example of generating a password
    openssl rand -base64 32 > root-ca-password.txt
    openssl rand -base64 32 > intermediate-ca-password.txt
    ```

2.  **Initialize the CA Locally:**
    Run the `step ca init` command on your local machine. This will create the necessary certificates and keys in your current directory.

    ```bash
    step ca init --name="Homelab Root CA" --dns="step-ca.step-ca.svc.cluster.local" \
      --address=":9000" --provisioner="admin" \
      --password-file=root-ca-password.txt \
      --provisioner-password-file=intermediate-ca-password.txt
    ```

3.  **Create Kubernetes Secrets:**
    Create the secrets in the `step-ca` namespace. These secrets will be used by the `step-ca` Helm chart.

    First, create the secrets for the passwords:
    ```bash
    # CA password
    kubectl create secret generic step-ca-step-certificates-ca-password -n step-ca \
      --from-file=password=root-ca-password.txt

    # Intermediate CA password
    kubectl create secret generic step-ca-step-certificates-provisioner-password -n step-ca \
      --from-file=password=intermediate-ca-password.txt

    # Certificate issuer password (also from your intermediate-ca-password.txt)
    kubectl create secret generic step-ca-step-certificates-certificate-issuer-password -n step-ca \
      --from-file=password=intermediate-ca-password.txt
    ```

    Next, create the TLS secrets. We will use `openssl` to decrypt the keys in memory and pipe them directly to `kubectl` to avoid writing the unencrypted key to disk.

    ```bash
    # Public certificates secret
    kubectl create secret generic step-ca-step-certificates-certs -n step-ca \
      --from-file=root_ca.crt=secrets/certs/root_ca.crt \
      --from-file=intermediate_ca.crt=secrets/certs/intermediate_ca.crt
   
    # Encrypted private keys secret
    kubectl create secret generic step-ca-step-certificates-secrets -n step-ca \
      --from-file=root_ca_key=secrets/secrets/root_ca_key \
      --from-file=intermediate_ca_key=secrets/secrets/intermediate_ca_key
    ```

    <!-- ```bash -->
    <!-- # Root CA certificates and keys -->
    <!-- openssl pkey -in secrets/root_ca_key -passin file:root-ca-password.txt | \ -->
      <!-- kubectl create secret tls step-ca-certs -n step-ca \ -->
        <!-- --cert=certs/root_ca.crt \ -->
        <!-- --key=/dev/stdin -->

    <!-- # Intermediate CA certificates and keys -->
    <!-- openssl pkey -in secrets/intermediate_ca_key -passin file:root-ca-password.txt | \ -->
      <!-- kubectl create secret tls step-ca-intermediate-certs -n step-ca \ -->
        <!-- --cert=certs/intermediate_ca.crt \ -->
        <!-- --key=/dev/stdin -->
    <!-- ``` -->
