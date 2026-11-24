# zot — OCI registry (staged, NOT yet deployed)

Zot OCI-registry fronting Garage S3 for blob storage. This is the staging
branch of what is intended to eventually replace / complement
`apps/base/docker-registry` (registry:2). **The `docker-registry` entry is
untouched** — both registries run against the same Garage bucket only if you
choose the same bucket; by default zot uses prefix `zot/` inside `docker-dev`
so it can coexist with the existing registry's objects.

## What's here

| File | Purpose |
|------|---------|
| `configmap.yaml` | `zot-config` ConfigMap with the zot v2 JSON config |
| `deployment.yaml` | 2 replicas, `ghcr.io/project-zot/zot:v2.1.8`, requests 500m/1Gi, limits 2 CPU/4Gi |
| `service.yaml` | ClusterIP `zot.zot.svc.cluster.local:5000` (in-cluster pulls) |
| `tailscale-lb.yaml` | Tailnet exposure `zot-mc.<tailnet>.ts.net:80` → 5000 via `tailscale.com/proxy-group` |
| `network-policy.yaml` | Ingress restricted to tailscale namespace + in-cluster |
| `namespace.yaml` | `zot` namespace |

Hostname `zot-mc` was checked against all other tailscale LB hostnames in the
repo (`postgres-rw`, `postgres-ro`, `s3-internal`, `mcp-mc-direct`,
`dnsutils`, `mcp-ts-placeholder`, `mcp-mc-direct`, `ai-*`, `deepseek-vllm`)
— no collision found.

## Vault secrets (OpenBao)

Wired in `apps.yaml` under the `zot` catalog entry (follows the
`tailscale-operator` example in AGENTS.md §6):

- VaultStaticSecret `zot-s3-creds` (auth `operator-auth`, mount `k8s`,
  path `zot/s3`, destination K8s Secret `zot-s3-creds`).
- cdk8s generates the dedicated VaultAuth + `operator-auth-sa`
  ServiceAccount and labels the `zot` namespace `vault-auth: enabled`.
- The pod consumes it via `envFrom: secretRef: zot-s3-creds`, expecting keys
  `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` (exactly as interpolated by the
  `${AWS_ACCESS_KEY_ID}` / `${AWS_SECRET_ACCESS_KEY}` placeholders in
  `config.json`).

**User action required:** seed OpenBao at `k8s/zot/s3` with the Garage
S3 credentials (keys `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`), and create
the Vault role binding for `operator-auth-sa` in the `zot` namespace
(`kubernetes_cluster_mc` mount).

## Garage S3 endpoint / bucket

- Endpoint: `http://garage.garage.svc.cluster.local:3900` (S3 API, verified
  from `apps/base/docker-registry/config/configmap.yaml`,
  `apps/base/forgejo/config/config-env.yaml`, and
  `bootstrap/base/garage/garage-values.yaml`).
- Region: `us-east-1` (garage's actual `s3_region`, from
  `bootstrap/base/garage/garage-values.yaml`).
- Bucket: `docker-dev` (the bucket docker-registry already uses — grep
  confirmed). Assumes zot is allowed to share it; if you want isolation,
  create a dedicated `zot` bucket and update both `configmap.yaml` and
  OpenBao creds.

## GC / retention

`gc` block in `config.json`: `enable: true`, `delay: 24h` (same fallback
shape as the supplied staging config).

**Pending schema verification against real zot v2 docs:** the desired
retention policy — keep 10 tags per repo, prune untagged manifests older
than 7 days. Zot v2 has `gc` plus `storage.retention`-style policy knobs
whose exact schema was NOT verified (fallback config was used per task
instructions). Re-check `https://zotregistry.dev` before production and
extend `config.json` accordingly.

## Pull-through mirrors (docker.io / ghcr.io) — NOT configured yet

Zot supports pull-through caching of upstream registries so cluster pulls
of docker.io / ghcr.io images can be served (and cached) from zot. The
config shape is roughly (per upstream docs, UNVERIFIED against zot v2.1.8):

```json
{
  "extensions": {
    "search": { "enable": true },
    "sync": {
      "enable": true,
      "registries": [
        {
          "urls": ["https://registry-1.docker.io"],
          "content": [
            { "prefix": "[**]", "destination": "/docker.io" }
          ],
          "onDemand": true,
          "tlsVerify": true
        },
        {
          "urls": ["https://ghcr.io"],
          "content": [
            { "prefix": "[**]", "destination": "/ghcr.io" }
          ],
          "onDemand": true,
          "tlsVerify": true
        }
      ]
    }
  }
}
```

**Needs schema verification** — `sync` vs `mirror` extension naming, the
`content[].prefix/destination` grammar, and `onDemand` behavior differ
between zot versions. Do not enable until verified against the
zotregistry.dev docs for v2.1.x.

## HA notes

- 2 replicas, shared Garage S3 (`docker-dev` bucket, `zot/` prefix) as the
  blob store.
- `cacheDriver` uses `boltlocal` at `/var/lib/zot-cache`, mounted from a
  per-replica `emptyDir` (`zot-cache`) so each replica keeps its own
  bolt DB — never share a bolt-local cache across replicas.
- `/var/lib/zot` (`storage.rootDirectory`) is also `emptyDir` per replica:
  blob content is stored in S3, the local dir only holds transient upload
  spool / staging state.
- **Caveat to verify before prod:** zot's `dedupe` and blob-cache semantics
  with a shared S3 backend — confirm whether concurrent replicas writing
  and GC'ing blobs against the same bucket/prefix are safe (zot docs
  recommend specific settings for shared-storage HA; not verified here).
- Container registry clients (containerd, docker, podman) hitting the
  ClusterIP service directly will round-robin between replicas; OCI
  manifest/blob GETs are safe to load-balance, PUTs rely on the S3
  backend for durability (verify multi-part upload behavior in the
  shared-S3 HA notes above).

## Wiring

- `apps.yaml`: `zot` catalog entry — `path: apps/base/zot/config`,
  vaultSecrets block, syncOptions `CreateNamespace=true` +
  `ServerSideApply=true`.
- `clusters/mc.yaml`: app `zot` in namespace `zot`, plus the same
  proxy-group annotation patch the other tailscale-exposed apps get
  (`ingress-proxy` → `mc-ingress-proxy`).
- `clusters/cc.yaml` deliberately NOT touched.

## Schema verification checklist (before production)

1. Confirm zot v2.1.x config schema for: `storage.s3[]` list form,
   `cacheDriver[]` `boltlocal` name/rootdirectory casing,
   `http.address`/`http.port`, and whether
   `storage.deleteEnabled` belongs at top level or under `storage`.
2. GC/retention policy keys (keep-N-tags, prune-untagged-7d).
3. Pull-through mirror (sync extension) config shape.
4. Shared-S3 HA semantics for dedupe/blob cache and concurrent GC.
