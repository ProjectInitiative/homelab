
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
  name: openbao-unseal-config
data:
  bao.hcl: |
    storage "raft" {
      path = "/bao/data"
      retry_join { leader_api_addr = "http://openbao-unseal-0.openbao-unseal-headless:8200" }
      retry_join { leader_api_addr = "http://openbao-unseal-1.openbao-unseal-headless:8200" }
      retry_join { leader_api_addr = "http://openbao-unseal-2.openbao-unseal-headless:8200" }
    }
    seal "pkcs11" {
      lib           = "/usr/lib/libtpm2_pkcs11.so"
      token_label   = "openbao-unseal-token"
      pin           = env("BAO_PKCS11_PIN") # Use environment variable for the PIN
      key_label     = "openbao-unseal-cluster-key"
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
  name: openbao-unseal-headless
spec:
  clusterIP: None
  selector:
    app: openbao-unseal
---
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: openbao-unseal
spec:
  selector:
    matchLabels:
      app: openbao-unseal
  template:
    metadata:
      labels:
        app: openbao-unseal
    spec:
      containers:
      - name: openbao
        image: openbao/openbao:latest
        args: ["server", "-config=/bao/config/bao.hcl"]
        ports:
        - containerPort: 8200
        env:
        - name: BAO_PKCS11_PIN # Inject the PIN from the k8s secret
          valueFrom:
            secretKeyRef:
              name: openbao-unseal-pin
              key: pin
        volumeMounts:
        - name: config
          mountPath: /bao/config
        - name: tpm-socket
          mountPath: /var/run/tpm2-abrmd/tpm2-abrmd.sock
      volumes:
      - name: config
        configMap:
          name: openbao-unseal-config
      - name: tpm-socket
        hostPath:
          path: /var/run/tpm2-abrmd/tpm2-abrmd.sock
          type: Socket
```

Once both the encrypted secret and this deployment file are in Git, Argo CD will sync them. The cluster will start, and the pods will auto-unseal using their local TPMs. You can then run `kubectl exec -ti <pod-name> -- bao operator init` to perform the one-time initialization of the Raft cluster.
