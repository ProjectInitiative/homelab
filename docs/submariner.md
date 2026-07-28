# Submariner — Cross-Cluster Networking

## Architecture

```
┌────────────────────────┐       ┌────────────────────────┐
│  cc (control cluster)  │       │  mc (main cluster)     │
│                        │       │                        │
│  submariner-k8s-broker │◄─────►│  submariner-operator   │
│  submariner-operator   │  VPN  │  pod CIDR: 10.42.0.0/16│
│  pod CIDR: 10.42.0.0/16│       │  svc CIDR: 10.43.0.0/16│
│  svc CIDR: 10.43.0.0/16│       │                        │
└────────────────────────┘       └────────────────────────┘
```

Both clusters share the same pod/service CIDRs — `globalnet: true` assigns unique per-cluster global IPs to avoid conflicts.

## Deployment Sequence

### Step 1 — Merge and sync (automatic)

The broker and operator are defined in `apps.yaml` + `clusters/*.yaml`.
The Argo CD CMP plugin generates the Application CRDs on sync.

| App | Cluster | Type |
|-----|---------|------|
| `submariner-k8s-broker` | cc | Broker (API + RBAC) |
| `submariner-operator` | cc | Operator (gateway, route-agent) |
| `submariner-operator` | mc | Operator (gateway, route-agent) |

### Step 2 — Extract broker info → store in Vault (manual bootstrap)

After the broker deploys on **cc**, it creates a connection-info secret.
That secret must be extracted and stored in Vault so both operators can connect.

```bash
# 1. Find the broker secret
kubectl get secrets -n submariner-k8s-broker

# 2. Extract fields and store in Vault
SECRET=$(kubectl get secrets -n submariner-k8s-broker -o name | head -1)

BROKER_URL=$(kubectl get "$SECRET" -n submariner-k8s-broker -o json | jq -r '.data.brokerURL // .data."broker-url" | @base64d')
CA_CRT=$(kubectl get "$SECRET" -n submariner-k8s-broker -o json | jq -r '.data."ca.crt" // .data."ca" | @base64d')
TOKEN=$(kubectl get "$SECRET" -n submariner-k8s-broker -o json | jq -r '.data.token | @base64d')
IPSec_PSK=$(kubectl get "$SECRET" -n submariner-k8s-broker -o json | jq -r '.data."ipsec.psk" // .data."IPsecPSK" // "" | @base64d')

vault kv put k8s/submariner/broker-info \
  brokerURL="$BROKER_URL" \
  ca.crt="$CA_CRT" \
  token="$TOKEN" \
  ipsec.psk="$IPSec_PSK"
```

### Step 3 — Operators connect (automatic)

The VaultStaticSecret on each cluster syncs the broker info from Vault to a K8s secret named `submariner-broker-info`. The operators detect it and establish tunnels.

```bash
# Verify on cc
kubectl get secret submariner-broker-info -n submariner-operator

# Verify on mc
kubectl get secret submariner-broker-info -n submariner-operator --context mc

# Check gateway status
kubectl get subgateways -n submariner-operator
kubectl get gateway -n submariner-operator
```

## Using cross-cluster services

After Submariner is healthy, you can reach services across clusters via:

```
# From mc, reach a service on cc
curl http://<service>.<namespace>.svc.clusterset.local:<port>

# From cc, reach a service on mc
curl http://<service>.<namespace>.svc.clusterset.local:<port>
```

Services need to be explicitly exported:

```yaml
apiVersion: submariner.io/v1
kind: ServiceExport
metadata:
  name: my-service
  namespace: my-namespace
```

This can be applied alongside the Service itself.

## Troubleshooting

```bash
# Check Submariner pods
kubectl get pods -n submariner-operator -o wide

# Check gateway connections
kubectl get subgateways -n submariner-operator -o yaml

# Check route agent
kubectl get daemonsets -n submariner-operator

# Check broker resources
kubectl get endpoints -n submariner-k8s-broker
kubectl get clusters -n submariner-k8s-broker

# Submariner diagnostics
kubectl get subctl diagnose

# If globalnet is on, services get a global IP
kubectl get globalingressips -A
```
