#!/bin/bash
# memguard-dgx — memory watchdog + forensics for DGX Spark (GB10 UMA) nodes.
#
# Runs as a privileged DaemonSet with hostPID so /proc is the HOST's view
# (cgroup working sets are blind to CUDA/UMA memory on GB10).
#
# Behavior:
#   - Continuous time-series: MemAvailable + top memory holders every loop.
#   - Escalation snapshots: WARN_GIB (attribution snapshots), full PRE-KILL
#     snapshot, then SIGKILL of the lane's rank processes.
#   - The PRE-KILL snapshot is the investigative artifact: per-process
#     Private_Dirty (real held memory), per-cgroup (per-pod) usage, slab,
#     PSI. Compare MemAvailable drop vs sum(Private_Dirty) growth: if
#     MemAvailable falls with no process accounting growing, memory is
#     leaking outside process accounting (driver/UMA allocations).
#
# All output goes to stdout (kubectl logs -n llm-test -l app=memguard-dgx)
# and a host file (survives pod restarts): /var/lib/llm-test/memguard/history.log
set -uo pipefail

WARN_GIB=${WARN_GIB:-8}        # start attribution snapshots
KILL_GIB=${KILL_GIB:-2.5}      # sustained floor -> kill countdown
HARD_GIB=${HARD_GIB:-1}        # instant kill floor
HOLD_S=${HOLD_S:-4}            # seconds under KILL_GIB before kill
INTERVAL=${INTERVAL:-10}       # normal sampling interval (s)
FAST_INTERVAL=${FAST_INTERVAL:-3}  # sampling interval under WARN_GIB
SNAPSHOT_EVERY=${SNAPSHOT_EVERY:-60}  # full snapshot cadence under WARN (s)
KILL_ENABLED=${KILL_ENABLED:-1}    # 1 = kill ranks; 0 = observe only (log WOULD KILL)
HIST=${HIST:-/var/lib/llm-test/memguard/history.log}
LANE_PAT='tensorfold|tf-dsv41|vllm'  # process cmdline patterns of the lanes

mkdir -p "$(dirname "$HIST")" 2>/dev/null || HIST=/tmp/memguard-history.log

ts() { date -u +%FT%TZ; }
log() { local l="[$(ts)] $*"; echo "$l"; echo "$l" >> "$HIST"; }
fcmp() { awk -v a="$1" -v b="$2" 'BEGIN{print (a<=b)?1:0}'; }
avail_gib() { awk '/^MemAvailable:/{printf "%.2f", $2/1048576}' /proc/meminfo; }

rotate_hist() {
  [ -f "$HIST" ] || return 0
  local sz; sz=$(stat -c%s "$HIST" 2>/dev/null) || return 0
  if [ "${sz:-0}" -gt 20971520 ]; then
    tail -n 5000 "$HIST" > "$HIST.tmp" && mv "$HIST.tmp" "$HIST"
  fi
}

# One process line: "PrivDirtyMiB RssMiB pid cmdline"
proc_line() {
  local p=$1 pid=${1#/proc/} cmd pd rss
  cmd=$(tr '\0' ' ' < "$p/cmdline" 2>/dev/null | cut -c1-110)
  [ -n "${cmd// }" ] || cmd=$(cat "$p/comm" 2>/dev/null)
  [ -r "$p/smaps_rollup" ] || return 0
  pd=$(awk '/^Private_Dirty:/{print int($2/1024)}' "$p/smaps_rollup" 2>/dev/null)
  [ -n "$pd" ] || return 0
  rss=$(awk '/^Rss:/{print int($2/1024)}' "$p/smaps_rollup" 2>/dev/null)
  printf '%s %s %s %s\n' "$pd" "${rss:-0}" "$pid" "$cmd"
}

top_procs() {
  local n=${1:-8}
  for p in /proc/[0-9]*; do proc_line "$p"; done 2>/dev/null | sort -rn | head -"$n"
}

lane_pids() {
  # Match on comm (executable name), not cmdline: cmdline matching catches
  # transient grep/tr children and can self-match. comm truncates to 15 chars
  # ("tensorfold-nati", "tf-dsv41-lanes", "vllm") — all covered by the globs.
  local p comm
  for p in /proc/[0-9]*; do
    comm=$(cat "$p/comm" 2>/dev/null) || continue
    case "$comm" in
      *tensorfold*|*tf-dsv41*|*vllm*) echo "${p#/proc/}" ;;
    esac
  done
}

snapshot() {
  local tag="$1" p
  log "=== SNAPSHOT ($tag) ==="
  log "--- meminfo (key, KiB) ---"
  grep -E '^(MemTotal|MemFree|MemAvailable|Cached|Buffers|Shmem|Slab|SReclaimable|SUnreclaim|Committed_AS|VmallocUsed):' /proc/meminfo | while read -r l; do log "$l"; done
  log "--- PSI memory ---"
  cat /proc/pressure/memory 2>/dev/null | while read -r l; do log "$l"; done
  log "--- top 15 processes by Private_Dirty (PrivDirtyMiB RssMiB pid cmd) ---"
  top_procs 15 | while read -r pd rss pid rest; do
    log "  ${pd} MiB priv, ${rss} MiB rss, pid=${pid}: ${rest}"
  done
  log "--- lane processes (detailed smaps_rollup) ---"
  for p in $(lane_pids); do
    log "  pid=$p cmd=$(tr '\0' ' ' < /proc/$p/cmdline 2>/dev/null | cut -c1-160)"
    grep -E '^(Rss|Pss|Private_Clean|Private_Dirty|Private|Anonymous|Swap|Locked):' /proc/$p/smaps_rollup 2>/dev/null | while read -r l; do log "    $l"; done
  done
  log "--- top container cgroups by memory.current ---"
  if [ -d /sys/fs/cgroup/kubepods.slice ]; then
    for f in /sys/fs/cgroup/kubepods.slice/*/kubepods-pod*/memory.current \
             /sys/fs/cgroup/kubepods.slice/kubepods-pod*/memory.current; do
      [ -r "$f" ] && echo "$(cat "$f" 2>/dev/null) $f"
    done | sort -rn | head -10 | while read -r b f; do
      log "  $(awk -v b="$b" 'BEGIN{printf "%.0f", b/1048576}') MiB  ${f#*kubepods.slice/}"
    done
  else
    log "  (cgroup v1 or kubepods.slice not found)"
  fi
  log "--- top slab entries (bytes) ---"
  awk 'NR>2 {printf "%s %d\n", $1, $3*1024}' /proc/slabinfo 2>/dev/null | sort -k2 -rn | head -5 | while read -r n b; do
    log "  ${b} ${n}"
  done
  log "=== END SNAPSHOT ==="
  rotate_hist
}

kill_lane() {
  local reason="$1" pids
  snapshot "PRE-KILL: $reason"
  pids=$(lane_pids | tr '\n' ' ')
  if [ -z "${pids// }" ]; then
    log "KILL($reason): no lane processes found (patterns: $LANE_PAT); nothing to kill"
    return 0
  fi
  if [ "$KILL_ENABLED" = "1" ]; then
    log "KILL($reason): SIGKILL lane pids: $pids (Conductor will recreate the pair)"
    kill -9 $pids 2>/dev/null
    sleep 2
    snapshot "POST-KILL: $reason"
  else
    log "OBSERVE MODE ($reason): KILL_ENABLED=0, WOULD KILL pids: $pids"
  fi
}

log "memguard-dgx started on $(cat /etc/hostname 2>/dev/null || hostname): WARN=${WARN_GIB}GiB KILL=${KILL_GIB}GiB HARD=${HARD_GIB}GiB HOLD=${HOLD_S}s KILL_ENABLED=${KILL_ENABLED}"

under_since=0
last_level=-1
last_snap=0
while true; do
  a=$(avail_gib); [ -n "$a" ] || a=999
  level=0
  [ "$(fcmp "$a" "$HARD_GIB")" = 1 ] && level=3
  [ "$level" = 0 ] && [ "$(fcmp "$a" "$KILL_GIB")" = 1 ] && level=2
  [ "$level" = 0 ] && [ "$(fcmp "$a" "$WARN_GIB")" = 1 ] && level=1

  now=$(date +%s)

  # Time-series line (the "trajectory up until the kill")
  t1=$(top_procs 1 | { read -r pd rss pid rest; echo "${rest%% *}: ${pd}MiB"; })
  log "mem avail=${a}GiB level=${level} top1=${t1:-?}"

  # Level transitions get a full snapshot
  if [ "$level" -ne "$last_level" ] && [ "$last_level" -ge 0 ]; then
    snapshot "level ${last_level} -> ${level} (avail=${a}GiB)"
  fi
  last_level=$level

  # Under WARN: periodic full snapshots to build the trajectory
  if [ "$level" -ge 1 ] && [ $((now - last_snap)) -ge "$SNAPSHOT_EVERY" ]; then
    snapshot "periodic level=${level} avail=${a}GiB"
    last_snap=$now
  fi

  # Kill logic: instant below HARD, sustained below KILL
  if [ "$level" -ge 3 ]; then
    kill_lane "hard floor ${HARD_GIB}GiB breached (avail=${a}GiB)"
    under_since=0
  elif [ "$level" = 2 ]; then
    [ "$under_since" = 0 ] && under_since=$now
    held=$((now - under_since))
    if [ "$held" -ge "$HOLD_S" ]; then
      kill_lane "avail=${a}GiB under ${KILL_GIB}GiB for ${held}s"
      under_since=0
    else
      log "kill countdown: ${held}s / ${HOLD_S}s under ${KILL_GIB}GiB"
    fi
  else
    under_since=0
  fi

  sleep "$([ "$level" -ge 1 ] && echo "$FAST_INTERVAL" || echo "$INTERVAL")"
done
