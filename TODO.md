# Infrastructure One-Offs

## Open Issues

### Tailscale IP rot — `vault-connection.yaml`
- **File:** `bootstrap/base/openbao-auth-config/config/vault-connection.yaml`
- **What:** The `VaultConnection` CR's `spec.address` hardcodes a Tailscale LoadBalancer IP (`100.88.134.95`). If the TS proxy recycles or the IP rotates, VSO loses connectivity to OpenBao and all VaultStaticSecrets stop syncing.
- **No fix yet:** Ideally we'd use a stable DNS name. The internal cluster DNS (`openbao.openbao:8200`) doesn't work for CC. A Tailscale MagicDNS name or a dedicated stable IP would solve this.

### Tailscale IP rot — `submariner-operator`
- **File:** `clusters/mc.yaml:148`
- **What:** `brokerK8sApiServer: "https://100.95.205.21:443"` is a hardcoded Tailscale IP for the Submariner broker on CC.
- **No fix yet:** Same problem — if TS IP rotates, submariner breaks. Needs a DNS-based resolution.

### Tailscale IP rot — `grafana-alloy`
- **File:** `apps.yaml:326,347`
- **What:** Loki and Mimir push URLs hardcode `http://100.119.112.42:3100` and `http://100.119.112.42:9090`.
- **No fix yet:** Same problem.

### VSO manager crashing (23 restarts)
- **Observed 2026-06-07:** `openbao-secrets-operator` manager container had 23 restarts, exit code 1.
- **Status:** This was a *symptom* of the vault-connection.yaml stale IP above. Now that the IP is fixed, needs monitoring to confirm it stabilises.

### TiKV/PD pods restarting
- **Observed:** All TiKV and PD pods in `tikv-cluster` restarted around June 1, some with 8+ restarts.
- **Status:** Currently stable, but the root cause (storage node issues? OOM?) is unknown. Monitor and investigate if repeats.
