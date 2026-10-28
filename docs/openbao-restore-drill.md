# OpenBao restore drill

Monthly automated test that proves the S3 snapshots are **actually
restorable** — including the key material in Bitwarden — by restoring the
latest snapshot into a throwaway single-node instance and verifying
content. A backup that has never been restored is a hope, not a backup.

## What it validates

| Stage | What | How |
|---|---|---|
| A (manual) | The **seal key** in Bitwarden is correct and retrievable | You place it in the drill pod; the drill refuses to proceed without it |
| B (auto) | The **snapshot in S3** is valid and restorable; the restored **keyring decrypts** with the seal key | Download → `raft snapshot restore` → restart → auto-unseal |
| C (manual) | The **recovery shares** in Bitwarden mint a working root token, and **secret content** survived | `generate-root` with 3 shares on the restored copy, then read a known path |

Everything runs on commodity hardware — no TPM, no production seal secret.
That's the point: it rehearses the "capstan burned down" scenario.

## Running it

**Scheduled**: CronJob `openbao-restore-drill` fires 06:00 UTC on the 1st of
each month (after that morning's 00:00 snapshot run), waits up to 48h for
the manual stages, then cleans itself up.

**On demand**:

```bash
kubectl --context mc -n openbao delete job openbao-restore-drill-manual --ignore-not-found; kubectl --context mc -n openbao create job openbao-restore-drill-manual --from=cronjob/openbao-restore-drill
```

## Walkthrough

**1. Watch the drill start:**

```bash
kubectl --context mc -n openbao logs -f -l job-name=openbao-restore-drill-manual
```

Stage A prints the exec command and waits for the seal key (48h deadline).

**2. Place the seal key** (from the Bitwarden entry: *OpenBao bootstrap
seal key* — 60-char value):

```bash
kubectl --context mc -n openbao exec -it openbao-restore-drill-manual-<suffix> -- sh
```

```bash
printf '%s' '<seal-key-value>' > /tmp/bao_seal_key
```

The drill detects it within 10s: init → unseal → download → restore →
restart → unseal again. Stage B takes ~2 minutes.

**3. Stage C — recovery-share test** (still in the pod shell):

```bash
export BAO_ADDR=http://127.0.0.1:8200
bao operator generate-root -generate-otp
bao operator generate-root -init -otp=<OTP>        # note NONCE + ENCODED token
printf '%s' '<recovery-share-1>' | bao operator generate-root -otp=<OTP> -nonce=<NONCE> -
printf '%s' '<recovery-share-2>' | bao operator generate-root -otp=<OTP> -nonce=<NONCE> -
printf '%s' '<recovery-share-3>' | bao operator generate-root -otp=<OTP> -nonce=<NONCE> -
bao operator generate-root -decode=<ENCODED> -otp=<OTP>
```

```bash
BAO_TOKEN=<decoded-root> bao kv get -mount=k8s garage/rpc
BAO_TOKEN=<decoded-root> bao token revoke <decoded-root>
```

If `garage/rpc` returns the RPC secret, content integrity is proven.

**4. Clean up:**

```bash
kubectl --context mc -n openbao delete job openbao-restore-drill-manual
```

## Pass / fail criteria

- **Stage A hangs forever** → the seal key in Bitwarden is missing or wrong.
  Fix the note; the drill is telling you your DR plan has a hole.
- **Stage B: restore fails / server never unseals** → snapshot invalid or
  seal mismatch. Check `$DRILL/server.log` in the pod. Backup pipeline bug.
- **Stage C: generate-root rejects all shares** → recovery shares are wrong
  or from an older generation. **This is the one that must never fail.**
- **Stage C: login + kv get works** → full pass. Everything in the DR chain
  (S3 snapshot, seal key, recovery shares, content) is proven.

## Optional stage D — prove the seal key is the irreplaceable artifact

While still on the drill instance (content verified in stage C):

```bash
rm /tmp/bao_seal_key
```

Restart the drill server (kill the bao process, start it again with the same
config). The server will come up **sealed** and stay sealed — then confirm:

```bash
printf '%s' '<recovery-share-1>' | bao operator unseal -
```

Expected: **rejected**. Recovery shares are "purely an authorization
mechanism" (OpenBao docs) — they cannot decrypt the root key. Only the seal
key can. This is the documented failure mode:

> "If the seal mechanism or its keys are permanently deleted, then the
> OpenBao cluster cannot be recovered, even from backups."

If a recovery share *does* unseal it, that's a finding worth an incident —
it would mean the drill instance's seal config isn't what we think it is.


## Restore requirements (for a real disaster)

All three artifacts, any two are useless without the third:

1. **Snapshot blob** — `s3://openbao-snapshots/` (garage, 30-day lifecycle
   handled by the agent)
2. **Seal key** — Bitwarden (*OpenBao bootstrap seal key*); also in the
   `openbao/openbao-bootstrap-seal-key` k8s secret and the node TPMs
3. **Recovery shares** — Bitwarden (5 shares, threshold 3) from
   `bao operator init` / rekey output

Restore command on a fresh instance (same static seal + key file):

```bash
bao operator raft snapshot restore <snapshot-file>
```

## Real-DR notes (from the openbao-tpm-init architecture)

The production cluster auto-unseals via the `openbao-tpm-init` sidecar
(bootstrap-init seals the seal key into each node's TPM; the unsealer sidecar
delivers it to the static seal). For a genuine from-scratch recovery:

1. **Recreate the `openbao-bootstrap-seal-key` secret first** — bootstrap-init
   reads it to seal the key into each node's TPM:

   ```bash
   kubectl --context mc -n openbao create secret generic openbao-bootstrap-seal-key --from-literal=seal-key='<value-from-bitwarden>'
   ```

   (Note: the sidecar's `cleanup_bootstrap_secret` is *designed* to delete this
   secret once the cluster is healthy, but the RBAC for that never existed —
   which is the only reason the 2026-10-23 TPM-reset recovery worked. The
   secret must be recreated from Bitwarden in any from-scratch recovery.)
2. Deploy the openbao sts — bootstrap-init seals the key into each node's TPM,
   the sidecar delivers it, the static seal auto-unseals.
3. Then restore the snapshot (`raft snapshot restore`) as above.

The restore drill deliberately skips this machinery: it tests that the
Bitwarden copy of the seal key alone is sufficient on commodity hardware.

## Known caveats

- The drill restores a 3-node cluster snapshot into a single node. Modern
  OpenBao re-establishes the local raft voter config on restore; if the
  drill server fails to reach quorum after restart (check
  `/drill/server.log`), that's a bug to escalate, not a user error.
- The snapshot contains the production token store — treat the drill pod as
  sensitive while it exists (it's namespaced to `openbao`, 48h max life).
- `test.blah.taildeab2.ts.net`-style DNS hangs from AI nodes are a separate
  known issue (see keel 2026-10-28 event); the drill only uses absolute
  FQDNs and is unaffected.
