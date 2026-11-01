# BCachefs NVMe repartition runbook — capstan1/2/3

**Date:** 2026-10-30 (rev 3 — promote restored via shared flash group) · Applies to: capstan1/2/3 (identical TEAM TM8FPD002T 1.9T NVMe + PM991a root + 5-device bcachefs pool, kernel 7.2.9)
**Design:** one flash group (`cache`) plays BOTH write pool and promote pool — the canonical bcachefs caching config (`foreground=promote=flash`, `background=hdd`). This needs no partition split: with write pool and promote target in the SAME group, the promote rule ("add a cached copy on read **if none exists on the target**") self-suppresses for fresh data (the p1 copy already satisfies it — no duplicate NVMe writes, the rev1 flaw), while migrated data gets exactly one flash copy per eviction cycle (the rev2 gap — read-heavy workloads like Immich keep flash-speed reads after their blocks migrate to HDD). Capacity contention is handled by bcachefs itself: under write pressure the allocator discards cached-only buckets LRU, so writes can never starve — promote copies just regenerate on the next read.

## Final layout (per node, nvme1n1 = 1900 GiB usable)

| Part | Size | Partlabel | Contents |
|---|---|---|---|
| p1 | ~1400 G | `bcachefs-flash` | bcachefs member, label `cache.nvme1` (**unchanged**) |
| p2 | ~480 G | `jfs-cache` | ext4 → `/mnt/jfs-cache` (JuiceFS node cache) |

Plus the SPCC SSD (sdb on cap1/2, sdd on cap3) **left exactly as is** (`cache.ssd1`, group `cache`).

**FS-wide targets** (persisted to superblock): `foreground_target=cache`, `promote_target=cache`, `background_target=hdd`.
Flash write+promote pool = 1.4 T + 1 T SPCC = **2.4 T**. The `nvme-cache` provisioner dir pins (`target=cache`) resolve to both flash devices unchanged — **no xattr work needed**.

**Read-tier layering:** hot blocks → JuiceFS p3 cache (no garage trip); warm → promoted flash copy on p1; cold → one HDD read then promoted. Read-heavy workloads (Immich-class) keep flash speed indefinitely without any per-directory config.

## Phase 0 — preflight (each node)

**Drain lesson (2026-10-31):** `bcachefs device evacuate` uses the throttled mover and can WEDGE (capstan2: D-state `bch-reconcile`, ~KB/s for hours, healthy disks — reboot cleared it). `bcachefs device remove` shunts the data off at full speed (~500 MB/s) in one step — **prefer `device remove` directly** and skip the evacuate-then-remove dance. The `Leaving 0` preflight is only needed if you insist on evacuating first.

```bash
ssh capstanH "sudo bcachefs fs usage /mnt/pool | grep -E 'Device|nvme|ssd|hdd'"
```
- **Cancel the SPCC evacuations** — the SPCC stays a normal member now:
```bash
ssh capstanH "sudo bcachefs device set-state rw /dev/sdb /mnt/pool"
```
(capstan3's SPCC is `/dev/sdd`.) Stale `Leaving` data on it clears on its own once targets are updated in Phase 1.
- Audit for stale pins (should only be `nvme-cache` with `target=cache`, which stays valid):
```bash
ssh capstanH "sudo getfattr -R -m bcachefs /mnt/pool 2>/dev/null | grep -B1 'bcachefs'"
```

## Phase 1 — remove NVMe, repartition, re-add (each node, after its drain)

```bash
ssh capstanH "sudo bcachefs device remove /mnt/pool /dev/nvme1n1"
```
```bash
ssh capstanH "sudo wipefs -a /dev/nvme1n1"
```
```bash
ssh capstanH "sudo sgdisk -o -n 1:0:+1400G -c 1:bcachefs-flash -n 2:0:0 -c 2:jfs-cache /dev/nvme1n1"
```
```bash
ssh capstanH "sudo mkfs.ext4 -L jfs-cache /dev/disk/by-partlabel/jfs-cache"
```
Re-add the flash member with the **same label as before** (group `cache` — keeps all dir pins valid):
```bash
ssh capstanH "sudo bcachefs device add --label=cache.nvme1 /mnt/pool /dev/disk/by-partlabel/bcachefs-flash"
```
Set fs-wide targets: **NO manual step — the capstan NixOS module enforces them** (`bcachefs-fs-options` in `modules/nixos/hosts/capstan/default.nix`, keyed by fs UUID: `foreground=cache.nvme1`, `promote=cache.ssd1`, `background=hdd`, `metadata=cache.nvme1`). This is the intended end state: writes on the NVMe partition, promotion on the SPCC (a different physical disk, so no duplicate-write hazard), migration to hdd. Do not set `fg=promote=cache` by hand — the module will fight it.
Verify:
```bash
ssh capstanH "sudo bcachefs fs usage /mnt/pool | grep -E 'Device|nvme|ssd|hdd' && df -h /mnt/pool /mnt/jfs-cache"
```

## Phase 2 — mount points (NixOS)

`modules/nixos/hosts/capstan` consumers already get `/mnt/jfs-cache` from the dotfiles change: `fileSystems."/mnt/jfs-cache"` on `/dev/disk/by-partlabel/jfs-cache`, `nofail` so hosts without the partition yet boot fine. Deploy per host with the usual flow **after** Phase 1 on that host.

## Phase 3 — JuiceFS mounts (GitOps)

`clusters/mc.yaml` `mountPodPatch` (already staged):
- **capstan1/2/3** node entries: `cache-dir=/mnt/jfs-cache`, `cache-size=102400`, `prefetch=8`, `buffer-size=1G`.
- **argo-root/argo-data** overrides: `cache-dir=/mnt/jfs-cache/argo` + bounded read cache (`cache-size=102400`, `prefetch=8`) — read-path only, no `--writeback` (uploads go RAM → Garage → bcachefs write pool; full blocks never touch the cache dir).

Deploy order: **Phase 1 + dotfiles deploy first** (dir must exist before mount pods reference it), then homelab sync, then bounce:
```bash
kubectl get pods -n kube-system -o wide | grep juicefs-capstan1
```
```bash
kubectl delete pod -n kube-system juicefs-capstan1-<pvc>-<suffix>
```
(CSI recreates each mount pod with the new options.) Then for argo:
```bash
virtctl stop argo && sleep 30 && virtctl start argo
```
Verify a mount pod picked the options up:
```bash
kubectl get pod -n kube-system juicefs-capstan1-pvc-eca4ccd6-0469-4d91-9ab3-0f7820bc2c87-pfrnzv -o jsonpath='{.spec.containers[0].command}' | grep -o 'cache-dir=[^,]*'
```

## Rollback / safety notes

- `device remove` is online; k3s keeps running throughout. Do it with Leaving=0 only.
- Between `remove` and `add` the fs briefly has no flash foreground target — writes fall back to hdd allocation for that window; run the `device add` right after.
- The pool mount is by fs UUID — adding/removing members never changes it; no fstab changes for `/mnt/pool`.
- JuiceFS cache dirs are disposable by definition: blow away `/mnt/jfs-cache` contents anytime (never `juicefs gc`, which is different).
- The gcache ring is deliberately NOT part of this (cache = disposable; add later).
- If promote ever needs to be disabled or scoped (e.g. it competes with a write-heavy window): per-directory `set-file-option --promote_target=none <dir>` or fs-wide `set-fs-option` — no repartition.
