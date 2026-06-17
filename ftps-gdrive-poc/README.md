# FTPS + Google Drive POC

Exposes a Google Drive folder over FTPS (FTP over TLS) via public hostPort on your lighthouse nodes.

Uses **GCP Workload Identity Federation (WIF)** — no long-lived OAuth tokens or service account keys. Your pod's Kubernetes SA token is automatically exchanged for a short-lived GCP access token.

## Architecture

```
Camera (internet)
     │
     ▼
lighthouse-den-1:21 / lighthouse-yul-1:21   (hostPort, one pod per node)
     │                     │
     └────────┬────────────┘
              ▼
        vsftpd (pasv_address=your.domain)
              │  /data/gdrive
              ▼
        rclone mount (FUSE, privileged)
              │
              ▼
        Google Drive API
              ▲
              │  Workload Identity Federation
              │  (K8s SA token → GCP access token)
              │
        GCP Workload Identity Pool
```

### Authentication Flow (Zero Long-Lived Secrets)

1. Pod has a Kubernetes ServiceAccount token at `/var/run/secrets/kubernetes.io/serviceaccount/token`
2. Google's ADC library reads `sts-creds.json` (mounted via ConfigMap) which says:
   *"Take this K8s token, go to this GCP Workload Identity Provider, and exchange it for a GCP access token"*
3. GCP validates the token against the JWKS you uploaded from your cluster
4. On success, GCP returns a short-lived access token scoped to your GCP SA
5. rclone uses that access token to call the Google Drive API
6. No service account JSON key ever touches the cluster

## Prerequisites

- Kubernetes cluster with [Service Account Token Volume Projection](https://kubernetes.io/docs/tasks/configure-pod-container/configure-service-account/#service-account-token-volume-projection) (enabled by default in k3s)
- `gcloud` CLI authenticated with a GCP project
- GCP Service Account with Google Drive API enabled and Drive access granted
- `kubectl` access to the cluster

## One-Time GCP Setup

Run the setup script on a machine with `kubectl` access to your cluster and `gcloud` authenticated:

```bash
# Replace with your GCP project ID and SA email
bash 03-gcp-wif-setup.sh <gcp-project-id> [gcp-sa-email]
```

This will:
1. Export your cluster's JWKS
2. Create a Workload Identity Pool
3. Create an OIDC provider pointing to your cluster's issuer URL + JWKS
4. Grant the `ftps-gdrive` K8s SA permission to impersonate your GCP SA
5. Generate `sts-creds.json` and output `03-gcp-auth-config.yaml`

## Deployment

### 1. Set the pasv_address

Edit `04-deployment.yaml` and replace `CHANGE-ME-YOUR-DOMAIN.com` with your public DNS name.

### 2. Apply

```bash
# Generate self-signed SSL certs
bash generate-certs.sh

# Apply everything in order
kubectl apply -f 01-rclone-config.yaml
kubectl apply -f 02-service-account.yaml
kubectl apply -f 03-gcp-auth-config.yaml
kubectl apply -f 04-deployment.yaml
kubectl apply -f 05-service.yaml
```

### 3. Point DNS

Create A records for each lighthouse node. Split cameras between them:

```
cam-node-1.yourdomain.com  A  <lighthouse-den-1 public IP>
cam-node-2.yourdomain.com  A  <lighthouse-yul-1 public IP>
```

Configuring each camera with a specific node IP is more reliable than round-robin
DNS, since passive FTP requires control and data to hit the same pod.

### 4. Connect

```bash
lftp -u ftpuser,changeme-in-cluster-config \
  -e "set ftp:ssl-force true; set ftp:ssl-protect-data true; ls" \
  cam-node-1.yourdomain.com
```

Configure your Reolink (or other) cameras with:
- **Server:** `cam-node-1.yourdomain.com` (or node 2)
- **Port:** `21`
- **User:** `ftpuser`
- **Pass:** `changeme-in-cluster-config`
- **FTPS:** Explicit TLS (AUTH TLS)
- **Verify cert:** Off (self-signed)

## Files

| File | Purpose |
|------|---------|
| `generate-certs.sh` | Creates a self-signed SSL cert and writes `02-ftps-ssl-certs.yaml` |
| `01-rclone-config.yaml` | ConfigMap with rclone.conf (uses `use_app_default_credentials`) |
| `02-service-account.yaml` | Kubernetes ServiceAccount for the pod |
| `03-gcp-wif-setup.sh` | Gcloud script to create WIF pool, provider, and credential config |
| `03-gcp-auth-config.yaml` | (generated) ConfigMap with sts-creds.json |
| `04-deployment.yaml` | DaemonSet: rclone FUSE mount + vsftpd FTPS server |
| `05-service.yaml` | ClusterIP service for internal DNS |

## Security Notes

- **No GCP service account keys** are stored anywhere in the cluster
- The `sts-creds.json` contains no secrets — just instructions for token exchange
- If your cluster's JWKS changes (e.g., node rebuild), re-run `03-gcp-wif-setup.sh` to re-upload the new keys
- The rclone container still requires `privileged: true` for FUSE mounts — this is the only privileged component
