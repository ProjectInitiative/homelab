# FTPS + Google Drive POC

Exposes a Google Drive folder over FTPS (FTP over TLS) via public NodePort on your lighthouse nodes.

## Architecture

```
Camera (internet) ──► lighthouse-den-1:21 ──► hostPort ──► vsftpd (pasv_address=your.domain)
                                     :21100-21102 ──► hostPort ──► vsftpd (passive data)
                                                                            │
                                                                            ▼ /data/gdrive
                                                                      rclone FUSE mount
                                                                            │
                                                                            ▼
                                                                      Google Drive API
```

A DaemonSet runs one pod on each lighthouse node (`lighthouse-den-1`, `lighthouse-yul-1`). Ports 21 + 21100-21102 are exposed via `hostPort` on each node's public IP. Point DNS A records at both IPs — configure each camera for a specific node (split them manually).

## Prerequisites

- [rclone](https://rclone.org/) installed on your local machine (for config generation)
- `kubectl` access to the cluster

## Deployment Steps

### 1. Generate your Google Drive rclone config

```bash
rclone authorize "drive"
```

Copy the JSON output into `01-rclone-config-secret.yaml` under the `token` field in `rclone.conf`.

### 2. Set the pasv_address

Before applying, edit `03-deployment.yaml` and replace `CHANGE-ME-YOUR-DOMAIN.com` with your actual public DNS name (e.g., `gdrive-ftps.yourdomain.com`). This is required for passive FTP data connections.

### 3. Apply

```bash
bash generate-certs.sh
kubectl apply -f 01-rclone-config-secret.yaml
kubectl apply -f 02-ftps-ssl-certs.yaml
kubectl apply -f 03-deployment.yaml
kubectl apply -f 05-service.yaml
```

### 4. Point DNS

Create A records for each lighthouse node. Split cameras between them:

```
camera-node-1.yourdomain.com  A  <lighthouse-den-1 public IP>
camera-node-2.yourdomain.com  A  <lighthouse-yul-1 public IP>
```

Or use a single A record with both IPs for round-robin, but note: FTP passive mode
requires control and data connections to hit the same node. With round-robin DNS,
data connections may land on the wrong node. **Configuring each camera with a
specific node IP is simpler and more reliable.**

### 5. Connect

```bash
lftp -u ftpuser,changeme-in-cluster-config \
  -e "set ftp:ssl-force true; set ftp:ssl-protect-data true; ls" \
  gdrive-ftps.yourdomain.com
```

Configure your Reolink (or other) cameras with:
- **Server:** `gdrive-ftps.yourdomain.com`
- **Port:** `21`
- **User:** `ftpuser`
- **Pass:** `changeme-in-cluster-config`
- **FTPS:** Explicit TLS (AUTH TLS)
- **Verify cert:** Off (self-signed)

## Files

| File | Purpose |
|------|---------|
| `generate-certs.sh` | Creates a self-signed SSL cert and writes `02-ftps-ssl-certs.yaml` |
| `01-rclone-config-secret.yaml` | K8s Secret with rclone.conf for Google Drive |
| `02-ftps-ssl-certs.yaml` | (generated) K8s Secret with SSL cert+key |
| `03-deployment.yaml` | DaemonSet: rclone FUSE mount + vsftpd FTPS server |
| `05-service.yaml` | ClusterIP service for internal DNS |

A DaemonSet runs one pod on each lighthouse node. `hostPort` exposes ports 21 and 21100-21102 directly on each node's public IP. Split cameras between the two nodes for HA.
