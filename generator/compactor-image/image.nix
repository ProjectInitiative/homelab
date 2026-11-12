# Garage LMDB compactor image — two tools, one image:
#
#   1. lmdb-swap-if-bloated   — initContainer in the garage STS (fail-open swap)
#   2. garage-compact-orchestrator — orchestrator Job (delete pod, wait, soak)
#
# See clusters/mc.yaml garage KUSTOMIZE_PATCH (init container) and
# bootstrap/base/garage/compactor-job.yaml (orchestrator Job + RBAC).
#
# Build:  nix-build generator/compactor-image
# Push:   same private-registry flow as cdk8s-cmp-plugin
#         -> ghcr.io/projectinitiative/garage-lmdb-compactor:latest
{ pkgs ? import <nixpkgs> {} }:

let
  swap-script = pkgs.writeShellScriptBin "lmdb-swap-if-bloated" ''
    #!/usr/bin/env bash
    set -u
    # --- Tunables (env overridable) ---
    META_DIR="''${META_DIR:-/mnt/meta}"
    SNAP_DIR="''${SNAP_DIR:-/snapshots}"
    BLOAT_RATIO="''${BLOAT_RATIO:-2}"            # integer: swap when live >= BLOAT_RATIO * snapshot
    SNAP_MAX_AGE_S="''${SNAP_MAX_AGE_S:-21600}"  # 6h: snapshot must be recent enough to resync from
    SNAP_MIN_AGE_S="''${SNAP_MIN_AGE_S:-300}"    # 5min: never trust a snapshot still being written
    PEER_MIN="''${PEER_MIN:-2}"
    PEER_HEALTH_TIMEOUT="''${PEER_HEALTH_TIMEOUT:-4}"
    DRY_RUN="''${DRY_RUN:-0}"
    NS="$(cat /var/run/secrets/kubernetes.io/serviceaccount/namespace 2>/dev/null || echo garage)"
    HEADLESS_SVC="''${HEADLESS_SVC:-garage-headless.''${NS}.svc.cluster.local}"

    log() { echo "[lmdb-swap] $*"; }

    # ---- 1. Live DB + newest settled snapshot ----
    # Live meta layout (garage v2.1.0): db.lmdb/ directory with data.mdb inside.
    dbdir="$META_DIR/db.lmdb"
    live_file="$dbdir/data.mdb"
    if [ ! -f "$live_file" ]; then
      log "SKIP: no $live_file (first boot or unexpected layout)"
      exit 0
    fi
    live_size="$(stat -c %s "$live_file")" || { log "SKIP: stat failed on $live_file"; exit 0; }

    snap=""
    for d in $(ls -1dt "''${SNAP_DIR}"/*/ 2>/dev/null); do
      f="''${d}db.lmdb"
      [ -f "$f" ] || continue
      mt="$(stat -c %Y "$f")"
      now="$(date +%s)"
      age=$(( now - mt ))
      [ "$age" -lt "$SNAP_MIN_AGE_S" ] && continue   # still being written
      [ "$age" -gt "$SNAP_MAX_AGE_S" ] && continue   # too stale to resync from
      snap="$f"
      break
    done
    if [ -z "$snap" ]; then
      log "SKIP: no settled snapshot in ''${SNAP_MIN_AGE_S}s..''${SNAP_MAX_AGE_S}s window"
      exit 0
    fi
    snap_size="$(stat -c %s "$snap")" || { log "SKIP: stat failed on $snap"; exit 0; }

    # ---- 2. Bloat ratio gate (integer math) ----
    if [ "$live_size" -lt $(( snap_size * BLOAT_RATIO )) ]; then
      log "SKIP: not bloated (live=''${live_size}B snap=''${snap_size}B ratio<''${BLOAT_RATIO})"
      exit 0
    fi

    # ---- 3. Peer readiness guard ----
    # garage-headless DNS returns only Ready endpoints; a pod in init is never
    # Ready, so self-exclusion is automatic. <2 peers = mass-boot or split
    # state -> never swap.
    peers="$(getent hosts "$HEADLESS_SVC" 2>/dev/null | awk '{print $1}' | sort -u)"
    n="$(printf '%s\n' "$peers" | grep -c . || true)"
    if [ "$n" -lt "$PEER_MIN" ]; then
      log "SKIP: only $n ready peer(s) (need $PEER_MIN) — mass-boot guard"
      exit 0
    fi

    # ---- 4. Peer health via tokenless /health (garage v2 leaves it open) ----
    for ip in $peers; do
      code="$(curl -s -o /dev/null -m "$PEER_HEALTH_TIMEOUT" -w '%{http_code}' "http://''${ip}:3903/health")"
      if [ "$code" != "200" ]; then
        log "SKIP: peer ''${ip} /health=''${code}"
        exit 0
      fi
    done

    # ---- 5. Dry-run / actual swap ----
    freed_mb=$(( ( live_size - snap_size ) / 1024 / 1024 ))
    if [ "$DRY_RUN" = "1" ]; then
      log "DRY-RUN: would swap $live_file (''${live_size}B) <- $snap (''${snap_size}B), ~''${freed_mb}MB freed, peers=$n ok"
      exit 0
    fi

    # free-space check: copy needs snap_size on the meta filesystem
    avail_kb="$(df -Pk "$META_DIR" | awk 'NR==2 {print $4}')"
    need_kb=$(( snap_size / 1024 + 1048576 ))   # snapshot + 1Gi headroom
    if [ "$avail_kb" -lt "$need_kb" ]; then
      log "SKIP: only ''${avail_kb}KB free on $META_DIR, need ~''${need_kb}KB"
      exit 0
    fi

    # Live layout (garage v2.1.0): db.lmdb/ is a DIRECTORY holding data.mdb
    # + lock.mdb; snapshots are a flat db.lmdb FILE. Swap targets the inner
    # data.mdb; backup kept inside db.lmdb/ (same fs -> rename is instant).
    dbdir="$META_DIR/db.lmdb"
    live_file="$dbdir/data.mdb"
    if [ ! -f "$live_file" ]; then
      log "SKIP: unexpected layout — no $live_file"
      exit 0
    fi
    ts="$(date -u +%Y%m%dT%H%M%SZ)"
    backup="$dbdir/data.mdb.precompact-''${ts}"
    if ! mv "$live_file" "$backup"; then
      log "FAIL: could not move $live_file aside"
      exit 1   # fail-open for the pod: init error is visible, garage not started on a mangled DB
    fi
    if ! cp "$snap" "$live_file"; then
      log "FAIL: copy failed — restoring original"
      mv "$backup" "$live_file"
      exit 1
    fi
    rm -f "$dbdir/lock.mdb"
    log "SWAPPED: $live_file <- $snap (~''${freed_mb}MB freed), backup=''${backup##*/}"
    exit 0
  '';

  # Orchestrator: runs as a k8s Job with SA garage-compactor. Deletes one
  # garage pod at a time; the STS recreates it and the init container decides
  # (fail-open) whether to swap. Hard pre-gate before touching anything.
  orchestrator-script = pkgs.writeShellScriptBin "garage-compact-orchestrator" ''
    #!/usr/bin/env bash
    set -euo pipefail
    : "''${NS:=garage}"
    : "''${STAGE:=dry}"           # dry | real
    : "''${SOAK_S:=600}"
    : "''${WAIT_TIMEOUT_S:=900}"
    LOCK="garage-compactor-lock"

    log() { echo "[orchestrator] $*"; }
    die() { echo "[orchestrator] ABORT: $*"; exit 1; }
    health() { # $1 = pod ip; 0 iff /health is 200
      local code
      code="$(curl -s -o /dev/null -m 4 -w '%{http_code}' "http://$1:3903/health" || echo 000)"
      [ "$code" = "200" ]
    }

    # ---- single-run lock (guards manual double-runs) ----
    if kubectl get configmap "$LOCK" -n "$NS" >/dev/null 2>&1; then
      die "lock $LOCK exists — another run in progress? (kubectl delete cm $LOCK -n $NS to clear)"
    fi
    kubectl create configmap "$LOCK" -n "$NS" >/dev/null
    trap 'kubectl delete configmap "$LOCK" -n "$NS" >/dev/null 2>&1 || true' EXIT

    # ---- pre-gate: 3 Ready pods, each /health 200 ----
    names="$(kubectl get pods -n "$NS" -o name | grep -E 'pod/garage-[0-9]+$' | sed 's|pod/||' | sort)"
    count="$(echo "$names" | grep -c . || true)"
    [ "$count" = "3" ] || die "expected 3 garage pods, got ($count): $names"
    declare -A ips
    for p in $names; do
      kubectl wait --for=condition=Ready "pod/$p" -n "$NS" --timeout=60s >/dev/null || die "$p not Ready"
      ip="$(kubectl get pod "$p" -n "$NS" -o jsonpath='{.status.podIP}')"
      ips[$p]="$ip"
      health "$ip" || die "$p ($ip) /health not 200"
      log "gate OK: $p ($ip)"
    done

    # ---- rolling pass: one pod at a time ----
    for p in $names; do
      for q in $names; do
        [ "$q" = "$p" ] && continue
        health "''${ips[$q]}" || die "peer $q unhealthy before deleting $p"
      done
      if [ "$STAGE" = "dry" ]; then
        log "DRY: gates pass; would delete $p (peers healthy, init container would swap if bloated)"
        continue
      fi
      log "deleting $p (init container swaps if bloated)"
      kubectl delete pod "$p" -n "$NS" --wait=false >/dev/null
      kubectl wait --for=condition=Ready "pod/$p" -n "$NS" --timeout="$WAIT_TIMEOUT_S" >/dev/null \
        || die "$p not Ready after ''${WAIT_TIMEOUT_S}s"
      log "$p Ready again — lmdb-compactor init log:"
      kubectl logs "pod/$p" -n "$NS" -c lmdb-compactor --tail=20 || true
      # refresh all pod IPs and re-verify the whole cluster
      for q in $names; do
        ip="$(kubectl get pod "$q" -n "$NS" -o jsonpath='{.status.podIP}')"
        ips[$q]="$ip"
        health "$ip" || die "$q ($ip) unhealthy after $p restart"
      done
      log "all healthy — soaking ''${SOAK_S}s before next node"
      sleep "$SOAK_S"
    done

    if [ "$STAGE" = "dry" ]; then
      log "DRY run complete — all gates pass on all nodes; rerun with STAGE=real to execute"
    else
      log "compaction pass complete for all nodes"
    fi
  '';
in
pkgs.dockerTools.buildLayeredImage {
  name = "garage-lmdb-compactor";
  tag = "latest";

  config = {
    Env = [ "PATH=/bin" ];
    # default entrypoint = init container behavior; the orchestrator Job
    # overrides command to run garage-compact-orchestrator
    Entrypoint = [ "${swap-script}/bin/lmdb-swap-if-bloated" ];
  };

  # runs as root (no User set): meta PVC files may be root-owned; the swap
  # needs rename/cp rights on /mnt/meta
  contents = [
    pkgs.bash
    pkgs.coreutils
    pkgs.curl
    pkgs.gawk
    pkgs.gnugrep
    pkgs.glibc # getent
    pkgs.kubectl
    orchestrator-script
  ];
}
