# FTPS + Google Drive POC

Exposes a Google Drive folder over FTPS (FTP over TLS) via your Tailscale tailnet, using rclone as the backend.

## Architecture

```
Client (Tailnet) ──► Tailscale Proxy ──► Service (gdrive-ftps:21)
                                               │
                                               ▼
                                         Deployment
                          ┌─────────────────────────────┐
                          │  [ftps-frontend (vsftpd)]   │◄── SSL cert secret
                          │  serves /data/gdrive        │
                          └──────────┬──────────────────┘
                                     │  shared emptyDir
                          ┌──────────▼──────────────────┐
                          │  [rclone-backend]           │◄── rclone.conf secret
                          │  mounts gdrive:/ → /data/gdrive │
                          │  (FUSE, privileged)         │
                          └─────────────────────────────┘
```

## Prerequisites

- Kubernetes cluster with [Tailscale Operator](https://tailscale.com/kubernetes-operator) installed
- [rclone](https://rclone.org/) installed on your local machine (for config generation)
- `kubectl` access to the cluster

## Deployment Steps

### 1. Generate your Google Drive rclone config

On your local machine:

```bash
# Install rclone if you don't have it
# macOS: brew install rclone
# Linux: sudo apt install rclone  or  sudo snap install rclone

# Generate the OAuth token (this opens a browser for Google auth)
rclone authorize "drive"

# Copy the JSON output, then edit 01-rclone-config-secret.yaml
# and paste it into the rclone.conf section:
#
# [gdrive]
# type = drive
# scope = drive
# token = {"access_token":"...","token_type":"Bearer","refresh_token":"...","expiry":"..."}
```

**Why this needs user interaction:** Google Drive requires OAuth 2.0. The first-time authorization must happen in a browser where you sign in to Google and grant rclone access to your Drive. There is no way to fully automate this step. You run `rclone authorize "drive"` on your local machine once, get the token, and paste it into the YAML.

> **Tip:** If you're on a headless machine, use `rclone config` instead and choose "headless machine" when it asks about auto-config — it will give you a URL to visit in your browser, then you paste the resulting code back.

### 2. Apply in order

```bash
# Generate self-signed SSL certs and create the secret
bash generate-certs.sh

# Apply everything
kubectl apply -f 01-rclone-config-secret.yaml
kubectl apply -f 02-ftps-ssl-certs.yaml
kubectl apply -f 04-deployment.yaml
kubectl apply -f 05-service.yaml
```

### 3. Find the Tailscale hostname & update pasv_address

```bash
# Get the Tailscale-assigned hostname
HOSTNAME=$(kubectl -n default get svc gdrive-ftps \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# Update the deployment with the correct pasv_address
kubectl -n default set env deploy/ftps-gdrive VSFTPD_PASV_ADDRESS="${HOSTNAME}"

# Restart the deployment
kubectl -n default rollout restart deploy/ftps-gdrive
```

### 4. Verify

```bash
# Check pod logs
kubectl -n default logs -l app=ftps-gdrive -c rclone-backend
kubectl -n default logs -l app=ftps-gdrive -c ftps-frontend

# If rclone can't mount (FUSE errors), check:
kubectl -n default exec deploy/ftps-gdrive -c rclone-backend -- ls -la /dev/fuse
```

### 5. Connect from your Tailnet

```bash
# FTPS (explicit TLS) — most FTPS clients
lftp -u ftpuser,changeme-in-cluster-config \
  -e "set ftp:ssl-force true; set ftp:ssl-protect-data true; ls" \
  gdrive-ftps.default.ts.net

# Or with plain ftp (no TLS):
# ftp gdrive-ftps.default.ts.net
```

## Files

| File | Purpose |
|------|---------|
| `generate-certs.sh` | Creates a self-signed SSL cert and writes `02-ftps-ssl-certs.yaml` |
| `01-rclone-config-secret.yaml` | K8s Secret with rclone.conf for Google Drive |
| `02-ftps-ssl-certs.yaml` | (generated) K8s Secret with SSL cert+key |
| `04-deployment.yaml` | Dual-container pod: rclone sidecar + vsftpd frontend |
| `05-service.yaml` | Tailscale LoadBalancer exposing ports 21 + 21100-21102 |

## Troubleshooting

**rclone mount fails with "fuse: device not found"**
The node may not have FUSE loaded. Fix:
```bash
kubectl -n default exec deploy/ftps-gdrive -c rclone-backend -- sh
# Inside the container:
mknod /dev/fuse c 10 229
chmod 666 /dev/fuse
exit
kubectl -n default delete pod -l app=ftps-gdrive
```

**Can't connect via FTPS client**
 Make sure `pasv_address` is set correctly via `kubectl get svc gdrive-ftps -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'`. The Tailscale hostname is required so the server tells clients the correct IP for passive data connections.

**Port 21 works but passive data connections fail**
 Ensure the Tailscale operator proxy forwards the entire port range (21100-21102). The service definition in `05-service.yaml` must list all passive ports explicitly.
