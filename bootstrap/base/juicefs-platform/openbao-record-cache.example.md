# OpenBao record: k8s/juicefs-cache/config
#
# MODELED EXACTLY ON k8s/juicefs/config (the prod tier) — same key schema, so
# job-format-cache.yaml and the CSI secret flow work unchanged. Put this record
# in OpenBao BEFORE syncing the juicefs-platform and postgres-cluster apps
# (both gain vaultSecrets entries pointing at this path — see apps.yaml).
#
#   bao kv put k8s/juicefs-cache/config \
#     name=juicefs-mc-cache \
#     storage=s3 \
#     bucket=https://<garage-s3-endpoint>/juicefs-mc-cache \
#     access_key=<GARAGE-ACCESS-KEY> \
#     secret_key=<GARAGE-SECRET-KEY> \
#     metaurl=postgres://juicefs_cache_user:<DB-PASSWORD>@postgres-rw.postgres-db.svc.cluster.local:5432/juicefs_cache \
#     username=juicefs_cache_user \
#     password=<DB-PASSWORD>
#
# Key-by-key (mirror of the prod record):
#
#   name        volume name as JuiceFS knows it. Reuse `juicefs-mc-cache` —
#               matches the bucket and keeps the format job's already-formatted
#               check meaningful.
#   storage     `s3` (Garage speaks the S3 API).
#   bucket      Full S3 URL of the garage bucket, e.g.
#               https://s3.garage.svc.cluster.local:3900/juicefs-mc-cache
#               — copy the exact endpoint form used in k8s/juicefs/config's
#               bucket key (same garage cluster).
#   access_key / secret_key
#               Garage key pair for the bucket. Reuse the existing key's
#               secret (GKf5de2532834574efaf46c63c, alias juicefs-mc-rw, RWO on
#               this bucket) or mint a fresh key granted RWO on
#               juicefs-mc-cache only. Not in git either way.
#   metaurl     Postgres URL to the DEDICATED cache metadata DB. The DB must
#               exist before juicefs format runs:
#                 kubectl -n postgres-db exec postgres-cluster-2 -c postgres -- \
#                   psql -U postgres -c 'CREATE DATABASE juicefs_cache OWNER juicefs_cache_user'
#               (juicefs-cache-database.yaml / juicefs-cache-role.yaml declare
#               it; the Database CR creates it on sync once the role secret
#               exists — if the operator is >= 1.25.0, nothing manual needed.)
#               Password is the one you put in the `password` key below —
#               postgres-cluster's vaultSecrets projects username/password from
#               this SAME record into the CNPG basic-auth Secret
#               juicefs-cache-postgres-creds, which juicefs-cache-role.yaml's
#               passwordSecret consumes. One source of truth.
#   username / password
#               The juicefs_cache_user DB credentials. Password must be set in
#               this record BEFORE the postgres-cluster app syncs the
#               DatabaseRole (it derives the CNPG secret from here).
#   passphrase  Passphrase PROTECTING THE RSA PEM (RISK-0045). Generate the
#               pem first, then put its passphrase here:
#
#                 openssl rand -base64 48            # <- the passphrase
#                 openssl genrsa -aes256 -out juicefs-cache.pem 4096
#                 head -2 juicefs-cache.pem           # must show: Proc-Type: 4,ENCRYPTED
#                 bao kv put -namespace=production -mount=k8s juicefs-cache/pem cert=@juicefs-cache.pem
#                 shred -u juicefs-cache.pem
#
#   envs        REQUIRED FOR MOUNTS (the 2026-11-19 outage: format worked,
#               mounts FATAL'd with "passphrase is required to private key").
#               The CSI driver injects the JSON map in this key as env vars
#               into every mount pod (juicefs-csi-driver docs,
#               security/encryption.md). Without it the mount pod has no
#               JFS_RSA_PASSPHRASE and cannot unwrap the key from metadata:
#
#                 bao kv patch -namespace=production -mount=k8s juicefs-cache/config \
#                   envs='{"JFS_RSA_PASSPHRASE":"<PEM-PASSPHRASE>"}'
#
#               (JSON-in-a-string, same passphrase as the pem record.) The
#               plain `passphrase` key above is what the FORMAT job reads;
#               `envs` is what MOUNT pods read. Both must exist.
#
#               The pem record (juicefs-cache/pem, key `cert`) is a SEPARATE
#               OpenBao record — mirrored by apps.yaml's juicefs-key-cache VSO
#               entry. The format job refuses to run without BOTH the pem and
#               a passphrase that actually decrypts it (verified pre-format
#               with openssl rsa -check). JuiceFS CE has NO symmetric
#               encryption; a volume formatted without a passphrase-protected
#               pem is permanently unencrypted.
#
# Do NOT put these values in git. The SC comment and this file describe the
# schema only.
