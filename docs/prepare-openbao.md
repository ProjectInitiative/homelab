
### \#\# 1. Prepare Each NixOS Host ❄️

This step configures the operating system on **all three** of your servers to enable the TPM and provide the necessary tools.

Add the following to your `/etc/nixos/configuration.nix` on each node:

```nix
services.tpm2-abrmd.enable = true;

environment.systemPackages = with pkgs; [
  tpm2-tools
  tpm2-pkcs11
  opensc
];
```

Then, apply the configuration on each node by running `sudo nixos-rebuild switch`.

-----

### \#\# 2. Initialize the TPM Token on Each Host 🔑

You must SSH into **each server individually** and run the following commands to create a PKCS\#11 token.

It is critical that you use the **exact same `--label` and `--userpin`** on all three servers.

  * On `server-1`:
    ```bash
    sudo tpm2_ptool.py init
    sudo tpm2_ptool.py addtoken --label="openbao-unseal-token" --userpin="<your-chosen-pin>"
    ```
  * On `server-2`:
    ```bash
    sudo tpm2_ptool.py init
    sudo tpm2_ptool.py addtoken --label="openbao-unseal-token" --userpin="<your-chosen-pin>"
    ```
  * On `server-3`:
    ```bash
    sudo tpm2_ptool.py init
    sudo tpm2_ptool.py addtoken --label="openbao-unseal-token" --userpin="<your-chosen-pin>"
    ```

-----

### \#\# 3. Create the Encrypted Kubernetes Secret 🤫

For your GitOps workflow with Argo CD, create a declarative YAML for the TPM PIN and encrypt it with SOPS.

1.  **Create the Secret Manifest**
    Create a file named `openbao-unseal-pin-secret.yaml`:
    ```yaml
    apiVersion: v1
    kind: Secret
    metadata:
      name: openbao-unseal-pin
    type: Opaque
    stringData:
      pin: "<your-chosen-pin>"
    ```
2.  **Encrypt the File**
    Run `sops` to encrypt the file before committing it to your Git repository.
    ```bash
    sops --encrypt --age <your-age-public-key> --in-place openbao-unseal-pin-secret.yaml
    ```

-----

### \#\# 4. Define and Deploy the K3s Resources ☸️

Create a single file named `openbao-unseal-cluster.yaml` containing all the necessary Kubernetes resources. This deployment securely references the secret you just created.

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: openbao-config
data:
  bao.hcl: |
    storage "raft" {
      path = "/bao/data"
      retry_join { leader_api_addr = "http://openbao-0.openbao-headless:8200" }
      retry_join { leader_api_addr = "http://openbao-1.openbao-headless:8200" }
      retry_join { leader_api_addr = "http://openbao-2.openbao-headless:8200" }
    }
    seal "pkcs11" {
      lib         = "/usr/lib/libtpm2_pkcs11.so"
      token_label = "openbao-token"
      pin         = env("BAO_HSM_PIN")
      key_label   = "openbao-unseal-key"
    }
    listener "tcp" {
      address         = "0.0.0.0:8200"
      cluster_address = "0.0.0.0:8201"
      tls_disable     = true
    }
    ui = false
    disable_performance_standby = true
---
apiVersion: v1
kind: Service
metadata:
  name: openbao-headless
spec:
  clusterIP: None
  selector:
    app: openbao
---
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: openbao
spec:
  selector:
    matchLabels:
      app: openbao
  template:
    metadata:
      labels:
        app: openbao
    spec:
      containers:
      - name: openbao
        image: openbao/openbao:latest
        args: ["server", "-config=/bao/config/bao.hcl"]
        ports:
        - containerPort: 8200
        env:
        - name: BAO_HSM_PIN
          valueFrom:
            secretKeyRef:
              name: openbao-unseal-pin
              key: pin
        # This variable tells the pkcs11 library how to connect to the TPM device
        - name: TPM2_PKCS11_TCTI
          value: "device:/dev/tpmrm0"
        volumeMounts:
        - name: config
          mountPath: /bao/config
        - name: data
          mountPath: /bao/data
        # Mount the TPM device directly into the container
        - name: tpm-device
          mountPath: /dev/tpmrm0
        # Mount the pkcs11 library from the NixOS host
        - name: pkcs11-lib
          mountPath: /usr/lib/libtpm2_pkcs11.so
          readOnly: true
      volumes:
      - name: config
        configMap:
          name: openbao-config
      - name: data
        hostPath:
          path: /var/lib/openbao
          type: DirectoryOrCreate
      # Define the hostPath for the TPM device
      - name: tpm-device
        hostPath:
          path: /dev/tpmrm0
          type: CharDevice
      # Define the hostPath for the pkcs11 library
      - name: pkcs11-lib
        hostPath:
          path: /run/current-system/sw/lib/libtpm2_pkcs11.so
          type: File

```

Once both the encrypted secret and this deployment file are in Git, Argo CD will sync them. The cluster will start, and the pods will auto-unseal using their local TPMs. You can then run `kubectl exec -ti <pod-name> -- bao operator init` to perform the one-time initialization of the Raft cluster.
