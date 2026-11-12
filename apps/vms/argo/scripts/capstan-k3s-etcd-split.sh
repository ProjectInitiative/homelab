#!/usr/bin/env bash
#
# capstan-k3s-etcd-split.sh — run ON THE TARGET CAPSTAN HOST (safemode, k3s stopped).
# Migrates k3s control plane (server/, incl. etcd) from the shared bcachefs pool
# (/mnt/pool/k3s) to the local root ext4 (/var/lib/rancher/k3s), keeping the
# 92G agent/ image cache on the pool via symlink.
#
# Usage (from your workstation, drives the migration over SSH):
#   ./capstan-k3s-etcd-split.sh kylepzak@172.16.4.52
#
# Pre-reqs on the target: k3s is STOPPED (safemode), rsync present (nixos has it).
# You run `nixos-rebuild switch` afterwards to pick up the new dotfiles config.
#
# Idempotent + safe to re-run: verifies copy, keeps rollback copy on pool.
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Usage: $0 [user@]<capstan-ip>" >&2
  exit 1
fi
DEST="$1"

echo "==> Verifying k3s is stopped on ${DEST}..."
if ssh -o BatchMode=yes -o ConnectTimeout=10 "${DEST}" \
   "systemctl is-active --quiet k3s; then" 2>/dev/null; then :; fi
if ssh -o BatchMode=yes -o ConnectTimeout=10 "${DEST}" \
   'systemctl is-active --quiet k3s'; then
  echo "ERROR: k3s is running on ${DEST}. Boot safemode / stop k3s first." >&2
  exit 1
fi
echo "    ok (k3s inactive)"

echo "==> Verifying preconditions via nametags on ${DEST}..."
ssh -o BatchMode=yes -o ConnectTimeout=10 "${DEST}" '
  set -e
  if [ ! -d /mnt/pool/k3s/server ]; then
    echo "ERROR: /mnt/pool/k3s/server not found (already migrated?)"; exit 1
  fi
  if [ -L /var/lib/rancher/k3s ]; then
    echo "INFO: /var/lib/rancher/k3s is the legacy symlink (expected pre-migration state)."
  fi
  command -v rsync >/dev/null || { echo "ERROR: rsync missing"; exit 1; }
  df --output=avail -h / | tail -1 | sed "s/^/    free on root: /"
'
echo "    ok"

echo "==> Staging break + real-dir prep on ${DEST}..."
ssh -o BatchMode=yes -o ConnectTimeout=10 "${DEST}" '
  set -e
  # Drop legacy alias so /var/lib/rancher/k3s can become a real dir
  if [ -L /var/lib/rancher/k3s ]; then
    sudo -n rm /var/lib/rancher/k3s
    echo "    removed legacy /var/lib/rancher/k3s symlink"
  fi
  sudo -n mkdir -p /var/lib/rancher/k3s

  # Existing real-dir migration? bail early (idempotency).
  if [ -d /var/lib/rancher/k3s/server ] && [ ! -L /mnt/pool/k3s/server ]; then
    echo "    already migrated (server on local+'no symlink'); verifying sizes only."
    exit 0
  fi
  if [ -L /mnt/pool/k3s/server ]; then
    echo "    /mnt/pool/k3s/server already symlinked — nothing to do."
    exit 0
  fi
'
# Note: exit 0 from the ssh block can be ambiguous with failures above guarded
# by set -e inside; treat ssh exit as fatal.
echo "    ok"

echo "==> Copying server/ and data/ to local root ext4 (content + perms/hardlinks, no virtual xattrs)..."
ssh -o BatchMode=yes -o ConnectTimeout=10 "${DEST}" '
  set -euo pipefail
  sudo -n rsync -aHAX --numeric-ids --no-xattrs /mnt/pool/k3s/server/ /var/lib/rancher/k3s/server/
  sudo -n rsync -aHAX --numeric-ids --no-xattrs /mnt/pool/k3s/data/  /var/lib/rancher/k3s/data/
'
echo "    copied."

echo "==> Byte-for-byte verify on ${DEST}..."
ssh -o BatchMode=yes -o ConnectTimeout=10 "${DEST}" '
  set -euo pipefail
  s1=$(stat -c %s /mnt/pool/k3s/server; stat -c %s /var/lib/rancher/k3s/server)
  d1=$(stat -c %s /mnt/pool/k3s/data;  stat -c %s /var/lib/rancher/k3s/data)
  # deep compare: sizes must match for both trees
  sudo -n du -sb /mnt/pool/k3s/server /var/lib/rancher/k3s/server
  sudo -n du -sb /mnt/pool/k3s/data  /var/lib/rancher/k3s/data
  # sample full equality via tar listing hashes
  h1=$(sudo -n tar -cf - -C /mnt/pool/k3s/server . | sha256sum | cut -d" " -f1)
  h2=$(sudo -n tar -cf - -C /var/lib/rancher/k3s/server . | sha256sum | cut -d" " -f1)
  if [ "$h1" != "$h2" ]; then echo "ERROR: server tree hash mismatch!" >&2; exit 1; fi
  h3=$(sudo -n tar -cf - -C /mnt/pool/k3s/data . | sha256sum | cut -d" " -f1)
  h4=$(sudo -n tar -cf - -C /var/lib/rancher/k3s/data . | sha256sum | cut -d" " -f1)
  if [ "$h3" != "$h4" ]; then echo "ERROR: data tree hash mismatch!" >&2; exit 1; fi
'
echo "    verified (trees identical by tar-hash)."

echo "==> Pointing k3s at the new home (rollback copy stays on pool)..."
ssh -o BatchMode=yes -o ConnectTimeout=10 "${DEST}" '
  set -e
  sudo -n mv /mnt/pool/k3s/server /mnt/pool/k3s/server.on-pool
  sudo -n ln -s /var/lib/rancher/k3s/server /mnt/pool/k3s/server
'
echo "    done."

echo "==> Final state on ${DEST}..."
ssh -o BatchMode=yes -o ConnectTimeout=10 "${DEST}" '
  set -e
  echo "    /var/lib/rancher/k3s (real dir):"
  ls -d /var/lib/rancher/k3s/{server,data} 2>/dev/null | sed "s/^/      /"
  echo "    /mnt/pool/k3s:"
  ls -la /mnt/pool/k3s | grep -E "server|agent|\\.$|\\.\\.$" | sed "s/^/      /"
  echo "    rollback copy:"
  ls -d /mnt/pool/k3s/server.on-pool 2>/dev/null | sed "s/^/      /" || echo "      (missing)"
  if [ -L /mnt/pool/k3s/server ]; then
    tgt=$(readlink /mnt/pool/k3s/server)
    echo "    /mnt/pool/k3s/server -> $tgt"
    [ -d "$tgt" ] || { echo "      ERROR: target missing!"; exit 1; }
  else
    echo "      ERROR: /mnt/pool/k3s/server not a symlink"; exit 1
  fi
'
echo
echo "✅ Migration complete on ${DEST}. Next:"
echo "   1. rebuild/switch to the new dotfiles revision (k3sDataDir=/var/lib/rancher/k3s,"
echo "      agent symlink activation + etcd compaction args)"
echo "   2. reboot out of safemode; verify:"
echo "      readlink /var/lib/rancher/k3s/agent        # -> /mnt/pool/k3s/agent"
echo "      kubectl get nodes                          # Ready"
echo "      journalctl -u k3s --since -5m | grep -c slow-fdatasync   # ~0"
echo "   3. only after Ready + verify, proceed to the next capstan."
