# Dev JuiceFS filesystem (`dev-juicefs`)

A separate JuiceFS filesystem for the dev node (astrolabe), fully disjoint from
the `juicefs-sc` / `juicefs-sc-cache` cluster filesystems: its own Garage
bucket and its own postgres database (`dev-juicefs`) with a dedicated role
(`dev_juicefs_user`), so dev experiments can never touch production data or
the production metadata engine.

## Topology

| Component    | Production (`juicefs-sc`)          | Dev (`dev-juicefs`)                  |
| ------------ | ---------------------------------- | ------------------------------------ |
| Metadata DB  | `juicefs` (owner `juicefs_user`)   | `dev-juicefs` (owner `dev_juicefs_user`) |
| Bucket       | production JuiceFS bucket          | `dev-juicefs` bucket on Garage       |
| OpenBao KV   | `k8s/juicefs/config`               | `k8s/dev-juicefs/config`             |

GitOps pieces (no manual k8s objects):

- `bootstrap/base/cnpg/database/dev-juicefs-database.yaml` — declarative
  Database CR (owner `dev_juicefs_user`).
- `bootstrap/base/cnpg/database/dev-juicefs-role.yaml` — DatabaseRole whose
  password comes from the `dev-juicefs-postgres-creds` secret.
- `apps.yaml` → `postgres-cluster` app → VSS `dev-juicefs-postgres-creds`
  projecting `k8s/dev-juicefs/config` (username/password only, basic-auth).

The one OpenBao record drives everything, mirroring how `juicefs/config`
serves both `juicefs-creds` and `juicefs-postgres-creds`:

```
name       = dev-juicefs
storage    = s3
bucket     = http://<garage-s3-endpoint>:3900/dev-juicefs
access-key = <garage rw key id for the bucket>
secret-key = <garage rw key secret>
metaurl    = postgres://dev_juicefs_user:<password>@<reachable-postgres-host>:5432/dev-juicefs
username   = dev_juicefs_user
password   = <password>
```

`metaurl` must be reachable from wherever the FS is mounted (astrolabe), not
just from inside the cluster — use whatever host serves postgres on your
tailnet. The in-cluster service DNS name only works for in-cluster mounts.

## Manual steps

1. **Create the bucket + key** (from a shell with the `garage` alias and
   `garage-create-bucket`, saves keys to files in the cwd):

   `garage-create-bucket dev-juicefs`

2. **Put the OpenBao record** (requires an active `bao-auth` session; fill in
   the values from step 1 and the chosen postgres password):

   `bao kv put -namespace=production -mount=k8s dev-juicefs/config name=dev-juicefs storage=s3 bucket=http://<garage-s3-endpoint>:3900/dev-juicefs access-key=<key-id> secret-key=<key-secret> metaurl='postgres://dev_juicefs_user:<password>@<reachable-postgres-host>:5432/dev-juicefs' username=dev_juicefs_user password=<password>`

   Do this BEFORE the DatabaseRole syncs: CNPG reads the password from the
   VSO-produced secret.

3. **Sync** the `postgres-cluster` Argo CD app (wave 40) so VSO materializes
   `dev-juicefs-postgres-creds` and CNPG reconciles the role and database.

4. **Format** from the dev node (inside a `bao-k8s-auth` or `bao-auth`
   session; the `dev-jfs-format` helper pulls the record and formats only if
   the DB reports unformatted):

   `dev-jfs-format`

5. **Mount** on the dev node:

   `dev-jfs-mount`

   Optional mountpoint override: `DEV_JFS_MOUNTPOINT=/path/to/mount dev-jfs-mount`.

The dev FS is intentionally NOT wired into a StorageClass: nothing in the
cluster mounts it. If a dev workload ever needs it, create a separate
`dev-juicefs-sc` StorageClass pointing at a `dev-juicefs-creds` secret (same
keys as `juicefs-creds`) rather than reusing `juicefs-sc`.
