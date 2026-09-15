#!/usr/bin/env python3
"""Sequential, self-cleaning JuiceFS local-cache benchmark controller.

Uses only the Python standard library and the in-cluster Kubernetes API. Child
Jobs emit fio JSON summaries; this controller persists incremental Markdown and
machine-readable results in a ConfigMap before deleting each test PVC/SC.
"""

from __future__ import annotations

import json
import os
import random
import signal
import ssl
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone
from typing import Any

NAMESPACE = os.getenv("POD_NAMESPACE", "llm-test")
NODE = os.getenv("TARGET_NODE", "astrolabe")
IMAGE = os.environ["BENCH_IMAGE"]
JUICEFS_IMAGE = os.getenv("JUICEFS_IMAGE", "juicedata/mount:ce-v1.3.1@sha256:ddba2917edee5af0e0dc367c79aae55f91de4666f8c13795d238b937d44e3b3c")
DATASET_GIB = int(os.getenv("DATASET_GIB", "8"))
RUNTIME_SECONDS = int(os.getenv("RUNTIME_SECONDS", "30"))
RAMP_SECONDS = int(os.getenv("RAMP_SECONDS", "5"))
REPETITIONS = int(os.getenv("REPETITIONS", "3"))
RANDOM_SEED = int(os.getenv("RANDOM_SEED", "38041"))
PROFILE_FILTER = {x for x in os.getenv("PROFILE_FILTER", "").split(",") if x}
if DATASET_GIB < 4 or DATASET_GIB % 4:
    raise SystemExit("DATASET_GIB must be at least 4 and divisible by four")
if REPETITIONS < 1:
    raise SystemExit("REPETITIONS must be positive")

RUN_ID = os.getenv("RUN_ID") or datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:5]
RUN_ID = "".join(c.lower() if c.isalnum() else "-" for c in RUN_ID).strip("-")[:24]
RESULT_CM = f"juicefs-cache-bench-{RUN_ID}"
PREFIX = f"jfsb-{RUN_ID}"

# `max-threads` is intentionally absent: JuiceFS CE 1.3.1 does not expose it.
# max-fuse-io is the supported FUSE dispatch-size variable in that release.
PROFILES = [
    {"id": "control", "description": "Clean JuiceFS defaults", "options": []},
    {"id": "direct", "description": "O_DIRECT with FUSE async direct-I/O capability", "options": ["async_dio"]},
    {
        "id": "meta",
        "description": "24h kernel/client metadata caches",
        "options": [
            "attr-cache=86400",
            "entry-cache=86400",
            "dir-entry-cache=86400",
            "open-cache=86400",
            "open-cache-limit=100000",
            "readdir-cache",
        ],
    },
    {"id": "fuse1m", "description": "1MiB maximum FUSE requests", "options": ["max-fuse-io=1M"]},
    {
        "id": "stripped",
        "description": "No block prefetch or read-ahead",
        "options": ["prefetch=0", "max-readahead=0"],
    },
    {
        "id": "meta-direct",
        "description": "Metadata caches plus direct I/O",
        "options": [
            "async_dio",
            "attr-cache=86400",
            "entry-cache=86400",
            "dir-entry-cache=86400",
            "open-cache=86400",
            "open-cache-limit=100000",
            "readdir-cache",
        ],
    },
    {
        "id": "combined",
        "description": "Metadata, direct I/O, 1MiB FUSE, no read-ahead",
        "options": [
            "async_dio",
            "attr-cache=86400",
            "entry-cache=86400",
            "dir-entry-cache=86400",
            "open-cache=86400",
            "open-cache-limit=100000",
            "readdir-cache",
            "max-fuse-io=1M",
            "prefetch=0",
            "max-readahead=0",
        ],
    },
]
if PROFILE_FILTER:
    PROFILES = [p for p in PROFILES if p["id"] in PROFILE_FILTER]
    unknown = PROFILE_FILTER - {p["id"] for p in PROFILES}
    if unknown:
        raise SystemExit(f"unknown PROFILE_FILTER values: {sorted(unknown)}")

PATTERNS = [
    {
        "id": "rand4k-psync-q1-j1",
        "description": "4KiB random, psync, QD1, 1 job",
        "args": ["--rw=randread", "--bs=4k", "--ioengine=psync", "--iodepth=1", "--numjobs=1"],
        "partition": False,
    },
    {
        "id": "rand4k-libaio-q64-j4",
        "description": "4KiB random, libaio, QD64, 4 jobs",
        "args": ["--rw=randread", "--bs=4k", "--ioengine=libaio", "--iodepth=64", "--numjobs=4"],
        "partition": True,
    },
    {
        "id": "seq4m-libaio-q16-j4",
        "description": "4MiB sequential, libaio, QD16, 4 jobs",
        "args": ["--rw=read", "--bs=4m", "--ioengine=libaio", "--iodepth=16", "--numjobs=4"],
        "partition": True,
    },
]


class ApiError(RuntimeError):
    pass


class Kubernetes:
    def __init__(self) -> None:
        host = os.environ["KUBERNETES_SERVICE_HOST"]
        port = os.getenv("KUBERNETES_SERVICE_PORT_HTTPS", "443")
        self.base = f"https://{host}:{port}"
        self.token = open("/var/run/secrets/kubernetes.io/serviceaccount/token").read().strip()
        ca = "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"
        self.context = ssl.create_default_context(cafile=ca)

    def request(self, method: str, path: str, body: Any | None = None, *, allow_404: bool = False) -> Any:
        data = None if body is None else json.dumps(body).encode()
        req = urllib.request.Request(
            self.base + path,
            data=data,
            method=method,
            headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"},
        )
        deadline = time.monotonic() + int(os.getenv("API_RETRY_SECONDS", "1800"))
        delay = 1.0
        while True:
            try:
                with urllib.request.urlopen(req, context=self.context, timeout=60) as response:
                    raw = response.read()
                    return json.loads(raw) if raw else None
            except urllib.error.HTTPError as exc:
                raw = exc.read().decode(errors="replace")
                if allow_404 and exc.code == 404:
                    return None
                if exc.code not in {429, 500, 502, 503, 504} or time.monotonic() >= deadline:
                    raise ApiError(f"{method} {path}: HTTP {exc.code}: {raw}") from exc
                print(f"transient Kubernetes HTTP {exc.code}; retrying {method} {path} in {delay:.0f}s", file=sys.stderr, flush=True)
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                if time.monotonic() >= deadline:
                    raise ApiError(f"{method} {path}: {exc}") from exc
                print(f"transient Kubernetes transport error; retrying {method} {path} in {delay:.0f}s: {exc}", file=sys.stderr, flush=True)
            time.sleep(delay)
            delay = min(30.0, delay * 2)

    def create(self, path: str, obj: dict[str, Any]) -> Any:
        try:
            return self.request("POST", path, obj)
        except ApiError as exc:
            # A lost POST response can leave the object successfully created.
            # Adopt it only when its exact benchmark run label matches.
            if "HTTP 409" not in str(exc):
                raise
            name = obj["metadata"]["name"]
            existing = self.get(path.rstrip("/") + "/" + name)
            if existing.get("metadata", {}).get("labels", {}).get("bench-run") != RUN_ID:
                raise
            return existing

    def get(self, path: str, *, allow_404: bool = False) -> Any:
        return self.request("GET", path, allow_404=allow_404)

    def put(self, path: str, obj: dict[str, Any]) -> Any:
        return self.request("PUT", path, obj)

    def delete(self, path: str) -> None:
        self.request(
            "DELETE",
            path,
            {"apiVersion": "v1", "kind": "DeleteOptions", "propagationPolicy": "Foreground"},
            allow_404=True,
        )


api: Kubernetes
results: list[dict[str, Any]] = []
owner_references: list[dict[str, Any]] = []
failures: list[str] = []
started = datetime.now(timezone.utc).isoformat()


def namespaced(resource: str, name: str | None = None, *, group: str = "api/v1") -> str:
    base = f"/{group}/namespaces/{NAMESPACE}/{resource}"
    return base if name is None else f"{base}/{name}"


def wait_for(predicate, description: str, timeout: int, interval: int = 3) -> Any:
    deadline = time.monotonic() + timeout
    last = None
    while time.monotonic() < deadline:
        last = predicate()
        if last:
            return last
        time.sleep(interval)
    raise TimeoutError(f"timed out waiting for {description}; last={last!r}")


def wait_pvc(name: str) -> None:
    wait_for(
        lambda: (obj := api.get(namespaced("persistentvolumeclaims", name), allow_404=True))
        and obj.get("status", {}).get("phase") == "Bound",
        f"PVC {name} Bound",
        300,
    )


# Pod logs are plain text, unlike the JSON resources handled by Kubernetes.request.
def pod_logs(job_name: str) -> str:
    selector = urllib.parse.quote(f"job-name={job_name}")
    pods = api.get(namespaced("pods") + f"?labelSelector={selector}").get("items", [])
    if not pods:
        return ""
    pod = sorted(pods, key=lambda p: p["metadata"]["creationTimestamp"])[-1]["metadata"]["name"]
    path = namespaced("pods", pod) + "/log"
    req = urllib.request.Request(api.base + path, headers={"Authorization": f"Bearer {api.token}"})
    with urllib.request.urlopen(req, context=api.context, timeout=60) as response:
        return response.read().decode(errors="replace")


def wait_job_and_logs(name: str, timeout: int) -> tuple[bool, str]:
    def finished():
        obj = api.get(namespaced("jobs", name, group="apis/batch/v1"), allow_404=True)
        if not obj:
            return None
        status = obj.get("status", {})
        if status.get("succeeded", 0) >= 1:
            return "succeeded"
        if any(c.get("type") == "Failed" and c.get("status") == "True" for c in status.get("conditions", [])):
            return "failed"
        return None

    state = wait_for(finished, f"Job {name} completion", timeout)
    return state == "succeeded", pod_logs(name)


def delete_and_wait(path: str, description: str, timeout: int = 180) -> None:
    api.delete(path)
    wait_for(lambda: api.get(path, allow_404=True) is None, f"{description} deletion", timeout)


def pvc(name: str, sc: str) -> dict[str, Any]:
    return {
        "apiVersion": "v1",
        "kind": "PersistentVolumeClaim",
        "metadata": {
            "name": name,
            "namespace": NAMESPACE,
            "labels": {"app": "juicefs-cache-bench", "bench-run": RUN_ID},
            "ownerReferences": owner_references,
        },
        "spec": {
            "accessModes": ["ReadWriteOnce"],
            "storageClassName": sc,
            "resources": {"requests": {"storage": "100Gi"}},
        },
    }


def child_job(name: str, claim: str, script: str, cpu: str, memory: str, image: str = IMAGE) -> dict[str, Any]:
    return {
        "apiVersion": "batch/v1",
        "kind": "Job",
        "metadata": {
            "name": name,
            "namespace": NAMESPACE,
            "labels": {"app": "juicefs-cache-bench-child", "bench-run": RUN_ID},
            "ownerReferences": owner_references,
        },
        "spec": {
            "ttlSecondsAfterFinished": 60,
            "backoffLimit": 0,
            "activeDeadlineSeconds": 3600,
            "template": {
                "metadata": {"labels": {"app": "juicefs-cache-bench-child", "bench-run": RUN_ID}},
                "spec": {
                    "restartPolicy": "Never",
                    "nodeSelector": {"kubernetes.io/hostname": NODE},
                    "containers": [
                        {
                            "name": "bench",
                            "image": image,
                            "imagePullPolicy": "Always",
                            "command": ["/bin/bash", "-lc"],
                            "args": [script],
                            "resources": {
                                "requests": {"cpu": cpu, "memory": memory},
                                "limits": {"cpu": cpu, "memory": memory},
                            },
                            "volumeMounts": [{"name": "data", "mountPath": "/data"}],
                        }
                    ],
                    "volumes": [{"name": "data", "persistentVolumeClaim": {"claimName": claim}}],
                },
            },
        },
    }


def seed_script() -> str:
    return f"""set -euo pipefail
file=/data/juicefs-bench-{RUN_ID}.bin
expected=$(( {DATASET_GIB} * 1024 * 1024 * 1024 ))
actual=$(stat -c%s "$file" 2>/dev/null || echo 0)
if [ "$actual" -ne "$expected" ]; then
  rm -f "$file"
  fio --name=seed --filename="$file" --rw=write --bs=4m --ioengine=libaio \
    --iodepth=16 --numjobs=1 --size={DATASET_GIB}Gi --direct=1 --end_fsync=1 \
    --output-format=normal
fi
sync
fio --version
echo SEED_COMPLETE
"""


def warm_script() -> str:
    return f"""set -euo pipefail
file=/data/juicefs-bench-{RUN_ID}.bin
test "$(stat -c%s "$file")" -eq $(( {DATASET_GIB} * 1024 * 1024 * 1024 ))
juicefs warmup --evict --threads 32 "$file" || true
complete=false
for pass in $(seq 1 16); do
  echo "warmup pass $pass/16"
  juicefs warmup --threads 32 "$file"
  sleep 2
  check=$(juicefs warmup --check --threads 32 "$file" 2>&1)
  printf '%s\n' "$check"
  if printf '%s\n' "$check" | grep -Eq '(^|[^0-9])100(\\.0+)?%'; then
    complete=true; break
  fi
done
[ "$complete" = true ]
printf 'MOUNT_INFO='; findmnt -T /data -n -o FSTYPE,OPTIONS || true
juicefs version
echo WARMUP_COMPLETE
"""


def fio_script(profile: dict[str, Any]) -> str:
    patterns = json.dumps(PATTERNS, separators=(",", ":"))
    return f"""set -euo pipefail
export PROFILE_ID={profile['id']!r} RUN_ID={RUN_ID!r}
export DATASET_GIB={DATASET_GIB} RUNTIME_SECONDS={RUNTIME_SECONDS} RAMP_SECONDS={RAMP_SECONDS}
export REPETITIONS={REPETITIONS} RANDOM_SEED={RANDOM_SEED}
export PATTERNS_JSON={patterns!r}
python3 - <<'PY'
import json, os, random, subprocess
patterns=json.loads(os.environ['PATTERNS_JSON'])
seed=int(os.environ['RANDOM_SEED'])
runtime=int(os.environ['RUNTIME_SECONDS']); ramp=int(os.environ['RAMP_SECONDS'])
reps=int(os.environ['REPETITIONS']); gib=int(os.environ['DATASET_GIB'])
file=f"/data/juicefs-bench-{{os.environ['RUN_ID']}}.bin"
assert os.stat(file).st_size == gib * 1024**3
order=[(r,p) for r in range(1,reps+1) for p in patterns]
random.Random(seed + sum(map(ord,os.environ['PROFILE_ID']))).shuffle(order)
for rep,p in order:
    args=['fio',f"--name={{p['id']}}",'--readonly','--direct=1',
          '--invalidate=1','--time_based=1',f'--runtime={{runtime}}',f'--ramp_time={{ramp}}',
          '--group_reporting=1','--norandommap=1',f'--randseed={{seed+rep}}','--randrepeat=1',
          '--lat_percentiles=1','--percentile_list=50:95:99:99.9','--output-format=json'] + p['args']
    if p['partition']:
        part=gib//4
        args += [f'--filename={{file}}',f'--size={{part}}Gi',f'--offset_increment={{part}}Gi']
    else:
        args += [f'--filename={{file}}',f'--size={{gib}}Gi']
    proc=subprocess.run(args,text=True,capture_output=True)
    if proc.returncode:
        print('FIO_STDERR='+proc.stderr.replace('\\n',' | '),flush=True)
        raise SystemExit(proc.returncode)
    doc=json.loads(proc.stdout); read=doc['jobs'][0]['read']
    lat=read.get('lat_ns') or read.get('clat_ns') or {{}}
    pct=lat.get('percentile',{{}})
    out={{
      'profile':os.environ['PROFILE_ID'],'pattern':p['id'],'description':p['description'],'repetition':rep,
      'iops':read.get('iops',0.0),'bw_bytes':read.get('bw_bytes',0.0),'lat_mean_ns':lat.get('mean',0.0),
      'lat_p50_ns':pct.get('50.000000',0.0),'lat_p95_ns':pct.get('95.000000',0.0),
      'lat_p99_ns':pct.get('99.000000',0.0),'lat_p999_ns':pct.get('99.900000',0.0),
      'total_ios':read.get('total_ios',0),'runtime_ms':read.get('runtime',0),'error':doc['jobs'][0].get('error',0),
    }}
    print('RESULT_JSON='+json.dumps(out,separators=(',',':')),flush=True)
PY
"""


def cleanup_script() -> str:
    return f"""set -euo pipefail
file=/data/juicefs-bench-{RUN_ID}.bin
if [ -e "$file" ]; then
  juicefs warmup --evict --threads 32 "$file" || true
  rm -f "$file"
fi
sync
echo CLEANUP_COMPLETE
"""


def parse_results(logs: str) -> list[dict[str, Any]]:
    parsed = []
    for line in logs.splitlines():
        if line.startswith("RESULT_JSON="):
            parsed.append(json.loads(line.removeprefix("RESULT_JSON=")))
    return parsed


def aggregate() -> list[dict[str, Any]]:
    rows = []
    for profile in PROFILES:
        for pattern in PATTERNS:
            samples = [r for r in results if r["profile"] == profile["id"] and r["pattern"] == pattern["id"]]
            if not samples:
                continue
            iops = [float(x["iops"]) for x in samples]
            lat = [float(x["lat_mean_ns"]) / 1e6 for x in samples]
            rows.append(
                {
                    "profile": profile["id"],
                    "pattern": pattern["id"],
                    "n": len(samples),
                    "iops_mean": statistics.fmean(iops),
                    "iops_stdev": statistics.stdev(iops) if len(iops) > 1 else 0.0,
                    "iops_cv_pct": 100 * statistics.stdev(iops) / statistics.fmean(iops) if len(iops) > 1 and statistics.fmean(iops) else 0.0,
                    "lat_mean_ms": statistics.fmean(lat),
                    "lat_p95_ms": statistics.fmean(float(x["lat_p95_ns"]) for x in samples) / 1e6,
                    "lat_p99_ms": statistics.fmean(float(x["lat_p99_ns"]) for x in samples) / 1e6,
                    "bw_mib_s": statistics.fmean(float(x["bw_bytes"]) for x in samples) / 2**20,
                }
            )
    return rows


def markdown() -> str:
    rows = aggregate()
    lines = [
        f"# JuiceFS cache benchmark `{RUN_ID}`",
        "",
        f"- Node: `{NODE}`",
        f"- Started: `{started}`",
        f"- Dataset: `{DATASET_GIB} GiB`, preseeded with O_DIRECT, evicted, then `juicefs warmup --threads=32`",
        f"- Repetitions: `{REPETITIONS}`; fio runtime/ramp: `{RUNTIME_SECONDS}s`/`{RAMP_SECONDS}s`",
        f"- Deterministic randomized execution seed: `{RANDOM_SEED}`",
        "- All measured fio reads use `--direct=1` to prevent Linux page-cache consumption.",
        "- Each profile uses an ephemeral 100Gi PVC, unique data blocks, and a dedicated benchmark cache root.",
        "",
        "| Profile | Pattern | n | IOPS mean | IOPS stdev | CV | Mean latency ms | p95 ms | p99 ms | MiB/s |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['profile']} | {r['pattern']} | {r['n']} | {r['iops_mean']:.2f} | "
            f"{r['iops_stdev']:.2f} | {r['iops_cv_pct']:.1f}% | {r['lat_mean_ms']:.4f} | "
            f"{r['lat_p95_ms']:.4f} | {r['lat_p99_ms']:.4f} | {r['bw_mib_s']:.2f} |"
        )
    lines += ["", "## Profiles", ""]
    for p in PROFILES:
        opts = ", ".join(p["options"]) or "defaults"
        lines.append(f"- **{p['id']}** — {p['description']}: `{opts}`")
    if failures:
        lines += ["", "## Failures", ""] + [f"- {x}" for x in failures]
    return "\n".join(lines) + "\n"


def persist() -> None:
    data = {"results.md": markdown(), "samples.json": json.dumps(results, indent=2, sort_keys=True), "failures.json": json.dumps(failures, indent=2)}
    path = namespaced("configmaps", RESULT_CM)
    current = api.get(path, allow_404=True)
    obj = {
        "apiVersion": "v1",
        "kind": "ConfigMap",
        "metadata": {"name": RESULT_CM, "namespace": NAMESPACE, "labels": {"app": "juicefs-cache-bench-results", "bench-run": RUN_ID}},
        "data": data,
    }
    if current:
        obj["metadata"]["resourceVersion"] = current["metadata"]["resourceVersion"]
        api.put(path, obj)
    else:
        api.create(namespaced("configmaps"), obj)


def run_profile(profile: dict[str, Any]) -> None:
    stem = f"{PREFIX}-{profile['id']}"[:52].rstrip("-")
    sc, claim = f"juicefs-bench-{profile['id']}", stem
    seed, warm, fio, clean = stem + "-seed", stem + "-warm", stem + "-fio", stem + "-clean"
    print(f"\n=== profile {profile['id']}: {profile['description']} ===", flush=True)
    for path, desc in [
        (f"/apis/batch/v1/namespaces/{NAMESPACE}/jobs/{seed}", seed),
        (f"/apis/batch/v1/namespaces/{NAMESPACE}/jobs/{warm}", warm),
        (f"/apis/batch/v1/namespaces/{NAMESPACE}/jobs/{fio}", fio),
        (f"/apis/batch/v1/namespaces/{NAMESPACE}/jobs/{clean}", clean),
        (namespaced("persistentvolumeclaims", claim), claim),
    ]:
        if api.get(path, allow_404=True):
            raise RuntimeError(f"refusing to overwrite pre-existing resource {desc}")
    try:
        api.create(namespaced("persistentvolumeclaims"), pvc(claim, sc))
        wait_pvc(claim)
        api.create(namespaced("jobs", group="apis/batch/v1"), child_job(seed, claim, seed_script(), "4", "2Gi"))
        ok, logs = wait_job_and_logs(seed, 1800)
        print(logs, flush=True)
        if not ok or "SEED_COMPLETE" not in logs:
            raise RuntimeError(f"seed Job {seed} failed")
        delete_and_wait(namespaced("jobs", seed, group="apis/batch/v1"), seed)

        api.create(namespaced("jobs", group="apis/batch/v1"), child_job(warm, claim, warm_script(), "4", "2Gi", JUICEFS_IMAGE))
        ok, logs = wait_job_and_logs(warm, 1800)
        print(logs, flush=True)
        if not ok or "WARMUP_COMPLETE" not in logs:
            raise RuntimeError(f"warmup Job {warm} failed")
        delete_and_wait(namespaced("jobs", warm, group="apis/batch/v1"), warm)

        api.create(namespaced("jobs", group="apis/batch/v1"), child_job(fio, claim, fio_script(profile), "8", "4Gi"))
        ok, logs = wait_job_and_logs(fio, max(1800, len(PATTERNS) * REPETITIONS * (RUNTIME_SECONDS + RAMP_SECONDS + 30)))
        print(logs, flush=True)
        parsed = parse_results(logs)
        expected = len(PATTERNS) * REPETITIONS
        invalid = [x for x in parsed if x["error"] or x["total_ios"] <= 0 or x["lat_mean_ns"] <= 0 or x["runtime_ms"] < RUNTIME_SECONDS * 900]
        if not ok or len(parsed) != expected or invalid:
            raise RuntimeError(f"fio Job {fio} failed, emitted {len(parsed)}/{expected} samples, invalid={len(invalid)}")
        results.extend(parsed)
        persist()
        delete_and_wait(namespaced("jobs", fio, group="apis/batch/v1"), fio)

        api.create(namespaced("jobs", group="apis/batch/v1"), child_job(clean, claim, cleanup_script(), "2", "1Gi", JUICEFS_IMAGE))
        ok, logs = wait_job_and_logs(clean, 600)
        print(logs, flush=True)
        if not ok:
            failures.append(f"{profile['id']}: cache cleanup Job failed")
        delete_and_wait(namespaced("jobs", clean, group="apis/batch/v1"), clean)
    finally:
        # Independent best-effort operations ensure one API error does not skip
        # later cleanup. OwnerReferences provide eventual GC if this pod dies.
        for job in (seed, warm, fio, clean):
            try:
                api.delete(namespaced("jobs", job, group="apis/batch/v1"))
            except Exception as exc:
                failures.append(f"cleanup {job}: {exc}")
        try:
            api.delete(namespaced("persistentvolumeclaims", claim))
            wait_for(lambda: api.get(namespaced("persistentvolumeclaims", claim), allow_404=True) is None, f"PVC {claim} deletion", 300)
        except Exception as exc:
            failures.append(f"cleanup {claim}: {exc}")


def main() -> int:
    global api
    api = Kubernetes()
    job_name = os.environ["CONTROLLER_JOB_NAME"]
    owner = api.get(namespaced("jobs", job_name, group="apis/batch/v1"))
    owner_references.append({
        "apiVersion": "batch/v1", "kind": "Job", "name": job_name,
        "uid": owner["metadata"]["uid"], "controller": False, "blockOwnerDeletion": False,
    })
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt("SIGTERM")))
    print(f"run={RUN_ID} node={NODE} profiles={[p['id'] for p in PROFILES]}", flush=True)
    order = list(PROFILES)
    random.Random(RANDOM_SEED).shuffle(order)
    persist()
    for profile in order:
        try:
            run_profile(profile)
        except Exception as exc:
            message = f"{profile['id']}: {type(exc).__name__}: {exc}"
            failures.append(message)
            print("ERROR " + message, file=sys.stderr, flush=True)
            persist()
    persist()
    print("\n" + markdown(), flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
