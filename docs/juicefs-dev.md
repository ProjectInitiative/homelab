# Dev JuiceFS filesystem (`juicefs-dev`)

A separate JuiceFS filesystem for the dev node (astrolabe), fully disjoint from
the `juicefs-sc` / `juicefs-sc-cache` cluster filesystems: its own Garage
bucket and its own postgres database (`juicefs-dev`) with a dedicated role
(`juicefs_dev_user`), so dev experiments can never touch production data or
the production metadata engine.

## Topology

| Component    | Production (`juicefs-sc`)          | Dev (`juicefs-dev`)                  |
| ------------ | ---------------------------------- | ------------------------------------ |
| Metadata DB  | `juicefs` (owner `juicefs_user`)   | `juicefs-dev` (owner `juicefs_dev_user`) |
| Bucket       | production JuiceFS bucket          | `juicefs-dev` bucket on Garage       |
| Encryption   | RSA key `k8s/juicefs/pem`          | RSA key `k8s/juicefs-dev/pem`        |
| OpenBao KV   | `k8s/juicefs/config`               | `k8s/juicefs-dev/config`             |

GitOps pieces (no manual k8s objects):

- `bootstrap/base/cnpg/database/juicefs-dev-database.yaml` — declarative
  Database CR (owner `juicefs_dev_user`).
- `bootstrap/base/cnpg/database/juicefs-dev-role.yaml` — DatabaseRole whose
  password comes from the `juicefs-dev-postgres-creds` secret.
- `apps.yaml` → `postgres-cluster` app → VSS `juicefs-dev-postgres-creds`
  projecting `k8s/juicefs-dev/config` (username/password only, basic-auth).

The one OpenBao record drives everything, mirroring how `juicefs/config`
serves both `juicefs-creds` and `juicefs-postgres-creds`:

```
name       = juicefs-dev
storage    = s3
bucket     = http://<garage-s3-endpoint>:3900/juicefs-dev
access-key = <garage rw key id for the bucket>
secret-key = <garage rw key secret>
metaurl    = postgres://juicefs_dev_user:<password>@<reachable-postgres-host>:5432/juicefs-dev
username   = juicefs_dev_user
password   = <password>
passphrase = <passphrase protecting the RSA pem>
```

The `passphrase` key mirrors `juicefs-creds`: the format helper exports it as
`JFS_RSA_PASSPHRASE` to unwrap the pem, and every client (mounts included)
needs it to parse the key stored in the metadata engine. It is only needed
because the pem is passphrase-protected; an unencrypted pem would not require
it.

The encryption key itself lives in a second record, mirroring `k8s/juicefs/pem`:

```
bao kv put -namespace=production -mount=k8s juicefs-dev/pem cert=@juicefs-dev.pem
```

Generated with `openssl genrsa -aes256 -out juicefs-dev.pem 4096`; the local
copy is shredded after the record is stored. JuiceFS CE has no symmetric
encryption — `juicefs format` only supports `--encrypt-rsa-key` (verified
against the v1.4.1 source bundled in CSI image v0.33.0; the format job's
`--encrypt-key` fallback branch is dead code). The dev format helper therefore
refuses to format when the pem record is missing instead of silently creating
an unencrypted filesystem.

`metaurl` must be reachable from wherever the FS is mounted (astrolabe), not
just from inside the cluster — use whatever host serves postgres on your
tailnet. The in-cluster service DNS name only works for in-cluster mounts.

## Manual steps

1. **Create the bucket + key** (from a shell with the `garage` alias and
   `garage-create-bucket`, saves keys to files in the cwd):

   `garage-create-bucket juicefs-dev`

2. **Put the OpenBao record** (requires an active `bao-auth` session; fill in
   the values from step 1 and the chosen postgres password):

   `bao kv put -namespace=production -mount=k8s juicefs-dev/config name=juicefs-dev storage=s3 bucket=http://<garage-s3-endpoint>:3900/juicefs-dev access-key=<key-id> secret-key=<key-secret> metaurl='postgres://juicefs_dev_user:<password>@<reachable-postgres-host>:5432/juicefs-dev' username=juicefs_dev_user password=<password> passphrase=<rsa-pem-passphrase>`

   Do this BEFORE the DatabaseRole syncs: CNPG reads the password from the
   VSO-produced secret.

3. **Sync** the `postgres-cluster` Argo CD app (wave 40) so VSO materializes
   `juicefs-dev-postgres-creds` and CNPG reconciles the role and database.

4. **Format** from the dev node (inside a `bao-k8s-auth` or `bao-auth`
   session; the `juicefs-dev-format` helper pulls the record and the pem and
   formats with `--encrypt-rsa-key`; it refuses to run if the pem record is
   missing):

   `juicefs-dev-format`

5. **Mount** on the dev node (the RSA key comes from the metadata engine; the
   helper only exports `JFS_RSA_PASSPHRASE` from the record):

   `juicefs-dev-mount`

   Optional mountpoint override: `JFS_DEV_MOUNTPOINT=/path/to/mount juicefs-dev-mount`.

The dev FS is intentionally NOT wired into a StorageClass: nothing in the
cluster mounts it. If a dev workload ever needs it, create a separate
`juicefs-dev-sc` StorageClass pointing at a `juicefs-dev-creds` secret (same
keys as `juicefs-creds`) rather than reusing `juicefs-sc`.
