# Submariner — Cross-Cluster Networking

## Architecture

```
cc (control cluster)          mc (main cluster)
┌────────────────────┐        ┌────────────────────┐
│ submariner-operator│        │ submariner-operator│
│   (broker mode)    │◄──────►│   (join mode)      │
│ pod: 10.42.0.0/16  │  VPN   │ pod: 10.42.0.0/16  │
│ svc: 10.43.0.0/16  │        │ svc: 10.43.0.0/16  │
└────────────────────┘        └────────────────────┘
```

Both clusters share the same CIDRs — `globalnet: true` assigns unique global IPs.

## Deployed Apps

| App | Cluster | Chart | Type |
|-----|---------|-------|------|
| `submariner-operator` | cc | `submariner-operator` 0.24.0 | Broker + operator |
| `submariner-operator` | mc | `submariner-operator` 0.24.0 | Join operator |

## Vault Secrets

The operator creates two VaultStaticSecrets via VaultSecrets abstraction:

| Vault Path | K8s Secret | Purpose |
|------------|-----------|---------|
| `submariner/broker-info` | `submariner-broker-info` | Broker connection info (token, CA, URL) |
| `submariner/ipsec-psk` | `submariner-ipsec-psk` | Shared IPsec pre-shared key |

## Bootstrap Steps

### Step 1 — Deploy the operator on cc

The cc operator deploys with `broker.server` set → the operator's `BrokerReconciler` creates broker resources automatically (namespace, RBAC, service account, CRDs).

After it deploys, a `Submariner` CR is created. The operator connects to itself as the broker using the placeholder token/CA values.

### Step 2 — Extract broker info and generate PSK

```bash
# Extract broker connection info
kubectl get secrets -n submariner-k8s-broker -o jsonpath='{.items[0].data}' | \
  jq '{brokerURL: ."broker-url" | @base64d, token: .token | @base64d, ca: ."ca.crt" | @base64d}'

# Store in Vault
BROKER_URL=$(kubectl get endpoints kubernetes -n default -o jsonpath='{.subsets[0].addresses[0].ip}:{.subsets[0].ports[?(@.name=="https")].port}')
CA_CRT=$(kubectl get secrets -n submariner-k8s-broker -o jsonpath='{.items[?(@.metadata.annotations.kubernetes\.io/service-account\.name)].data.ca\.crt}' | base64 -d)
TOKEN=$(kubectl get secrets -n submariner-k8s-broker -o jsonpath='{.items[?(@.metadata.annotations.kubernetes\.io/service-account\.name)].data.token}' | base64 -d)

vault kv put k8s/submariner/broker-info \
  brokerURL="$BROKER_URL" \
  ca.crt="$CA_CRT" \
  token="$TOKEN"

# Generate and store IPsec PSK
PSK=$(LC_CTYPE=C tr -dc 'a-zA-Z0-9' < /dev/urandom | fold -w 64 | head -n 1)
vault kv put k8s/submariner/ipsec-psk \
  psk="$PSK"
```

### Step 3 — VaultStaticSecret syncs (automatic)

The VaultStaticSecret on each cluster creates:
- `submariner-broker-info` — from `submariner/broker-info`
- `submariner-ipsec-psk` — from `submariner/ipsec-psk`

These secrets appear as `submariner-broker-info` and `submariner-ipsec-psk` in the `submariner-operator` namespace on both clusters.

### Step 4 — Verify

```bash
# Check gateway status
kubectl get subgateways -n submariner-operator -o wide

# Check clusters registered with broker
kubectl get clusters -n submariner-k8s-broker

# Check operator logs
kubectl logs -n submariner-operator deployment/submariner-operator
```

## Using cross-cluster services

Services need to be exported:

```yaml
apiVersion: submariner.io/v1
kind: ServiceExport
metadata:
  name: my-service
  namespace: my-namespace
```

Then reachable from the other cluster at:
```
<service>.<namespace>.svc.clusterset.local:<port>
```

## Verified Secret Contract (submariner-operator 0.24)

From operator source (release-0.24 `submariner_controller.go`), the broker
secret named by `brokerK8sSecret` is read for exactly two keys:

| Key | Format | Notes |
|---|---|---|
| `token` | raw SA token | overrides `brokerK8sApiServerToken` |
| `ca.crt` | raw PEM (unencoded) | operator base64-encodes internally; may be omitted |

The API server URL comes from the CR spec (`brokerK8sApiServer`), NOT the
secret — no `brokerURL` key is consumed. `brokerK8sApiServer` must be
scheme-less (admiral prepends `https://`).

PSK secret: literal key `psk` (libreswan mounts
`/var/run/secrets/submariner.io/<secretName>/psk`).

Values are stored RAW in OpenBao KV (`k8s/submariner/broker-info`,
`k8s/submariner/ipsec-psk`) — VSO base64-encodes at sync time.

## OpenBao Namespace Gotcha

OpenBao runs with enterprise-style namespaces (`production`). Every
VaultAuth/VaultStaticSecret MUST set `namespace: production` (apps.yaml
`vaultSecrets.namespace`); without it VSO authenticates against the root
namespace where no kubernetes_cluster_* mounts exist → 403 permission
denied.

## Broker RBAC

The token stored in broker-info is for SA `submariner-broker-admin` in
cc's `submariner-k8s-broker` namespace. It needs a Role (RoleBinding) in
that namespace covering submariner.io clusters/endpoints + core secrets/
configmaps/serviceaccounts + lighthouse serviceexports/serviceimports.

## Gateway Nodes

The submariner-gateway DaemonSet only schedules on nodes labeled
`submariner.io/gateway=true`. mc: capstan1 labeled. cc: needs one labeled
node once its operator comes up.
