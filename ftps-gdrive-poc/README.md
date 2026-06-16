# FTPS + Google Drive POC

Exposes a Google Drive folder over FTPS (FTP over TLS) via your Tailscale tailnet, using rclone's built-in FTP server.

## Architecture

```
Client (Tailnet) ──► Tailscale Proxy ──► Service (gdrive-ftps:21)
                                               │
                                               ▼
                                         Deployment
                          ┌──────────────────────────────┐
                          │  [rclone-ftps]               │
                          │  rclone serve ftp gdrive:/   │
                          │  TLS: --cert / --key         │◄── SSL cert secret
                          │  Auth: --user / --pass       │
                          │  Config: /config/rclone.conf │◄── rclone config secret
                          └──────────────────────────────┘
```

No FUSE, no privileged containers, no sidecars — just rclone serving FTP directly from the Google Drive API.

## Prerequisites

- Kubernetes cluster with [Tailscale Operator](https://tailscale.com/kubernetes-operator) installed
- [rclone](https://rclone.org/) installed on your local machine (for config generation)
- `kubectl` access to the cluster

## Deployment Steps

### 1. Generate your Google Drive rclone config

On your local machine:

```bash
# Generate the OAuth token (opens browser for Google auth)
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
kubectl apply -f 03-deployment.yaml
kubectl apply -f 05-service.yaml
```

### 3. Verify

```bash
# Check pod logs
kubectl -n default logs -l app=ftps-gdrive

# Test with any FTPS client from your Tailnet
lftp -u ftpuser,changeme-in-cluster-config \
  -e "set ftp:ssl-force true; set ftp:ssl-protect-data true; ls" \
  gdrive-ftps.default.ts.net
```

## Files

| File | Purpose |
|------|---------|
| `generate-certs.sh` | Creates a self-signed SSL cert and writes `02-ftps-ssl-certs.yaml` |
| `01-rclone-config-secret.yaml` | K8s Secret with rclone.conf for Google Drive |
| `02-ftps-ssl-certs.yaml` | (generated) K8s Secret with SSL cert+key |
| `03-deployment.yaml` | Single container: rclone serve ftp with TLS |
| `05-service.yaml` | Tailscale LoadBalancer exposing ports 21 + 21100-21102 |

## Troubleshooting

**Can't connect via FTPS client**
 Ensure the pod is running (`kubectl get pods -l app=ftps-gdrive`). Check logs with `kubectl logs -l app=ftps-gdrive`. Verify the rclone config is correct by execing in: `kubectl exec deploy/ftps-gdrive -- cat /config/rclone.conf`.

**Port 21 works but passive data connections fail**
 The Tailscale proxy must forward the entire port range (21100-21102). The service in `05-service.yaml` lists all passive ports explicitly — verify they're present.
