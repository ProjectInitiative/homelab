#!/usr/bin/env python3
"""Generic Hugging Face cache puller/deleter for the shared model volume.

Model-agnostic: declare repos to pull and/or delete as parameters. Downloads are
streamed by this script and rate-limited *in code* (a single thread-safe token
bucket shared across every file and every repo), so a large preload caps at RATE
bytes/sec and leaves the rest of the site's bandwidth for work / household.

Concurrency:
  - Repos are pulled in parallel (bounded by MAX_REPO_WORKERS).
  - Within each repo the files download in parallel (bounded by MAX_FILE_WORKERS).
  - All workers share one RateLimiter, so aggregate bandwidth never exceeds RATE
    no matter how many threads run.
  - Deletes also run in parallel (bounded by MAX_DELETE_WORKERS).
  Note: HuggingFace's snapshot_download itself parallelises files (max_workers),
  but we replaced it with a custom streaming downloader to enforce the in-code
  rate cap, so we re-add file-level concurrency here.

Parameters (env):
  HF_HOME            required   HF cache root (default /models/.cache/huggingface)
  PULL_MODELS        optional   comma-separated 'repo[@revision][#pattern|pattern]'
                                entries. Optional '#'-delimited include patterns (fnmatch
                                globs against repo-relative paths, '|' between them)
                                enable PARTIAL repo pulls — e.g. two shards out of a
                                48-shard checkpoint:
                                  org/model@<sha>#model-00047-of-00048.safetensors|model-00048-of-00048.safetensors
                                When patterns are present only matching files download and
                                refs/main is NOT written (a partial tree must never be
                                resolvable by repo id — reference the snapshot by path).
  DELETE_MODELS      optional   comma-separated HF repo ids (or bare cache dirs like models--org--name)
  RATE               optional   max bytes/sec across all pulls (default 104857600 = 100 MiB/s; 0 = unlimited)
  MAX_FILE_WORKERS   optional   concurrent file downloads total (default 8)
  MAX_REPO_WORKERS   optional   concurrent repos being pulled (default 2)
  MAX_DELETE_WORKERS optional   concurrent deletes (default 4)
  HF_TOKEN           optional   token for gated / rate-limited repos
  HF_ENDPOINT        optional   override the Hugging Face endpoint
"""
import fnmatch
import os
import sys
import time
import shutil
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

DEFAULT_RATE = 104857600  # 100 MiB/s


def log(*a):
    print("[puller]", *a, flush=True)


def env_int(name, default):
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


def cache_dirname(ref):
    if "/" in ref:
        return "models--" + ref.replace("/", "--")
    return ref


def parse_spec(spec):
    """'repo[@revision][#glob|glob]' -> (repo, revision_or_None, [include globs]).

    '#' never appears in HF repo ids or commit SHAs, so it is a safe delimiter.
    Backward compatible: a spec without '#' pulls the full repo, exactly as
    before.
    """
    body, _, pat_str = spec.partition("#")
    includes = [p.strip() for p in pat_str.split("|") if p.strip()]
    repo, rev = (body.rsplit("@", 1) if "@" in body else (body, None))
    return repo, rev, includes


class RateLimiter:
    """Thread-safe aggregate rate limiter (pacing).

    Each chunk reserves `n/rate` seconds on a shared virtual timeline; the worker
    sleeps until its slot. This caps the *aggregate* throughput at `rate` bytes/sec
    no matter how many threads are downloading concurrently, and avoids the
    overshoot a naive shared credit bucket gets under concurrency.
    """

    def __init__(self, rate):
        self.rate = float(rate)
        self.lock = threading.Lock()
        self.next_ok = 0.0  # monotonic deadline for the next byte budget

    def wait(self, n):
        budget = n / self.rate if n > 0 else 0.0
        with self.lock:
            now = time.monotonic()
            if now > self.next_ok:
                self.next_ok = now
            self.next_ok += budget
            deadline = self.next_ok
        delay = deadline - time.monotonic()
        if delay > 0:
            time.sleep(delay)


def _delete_one(cache_root, ref):
    d = cache_dirname(ref)
    hit = False
    for base in (os.path.join(cache_root, "hub"), cache_root):
        p = os.path.join(base, d)
        if os.path.isdir(p):
            log("deleting", p)
            shutil.rmtree(p, ignore_errors=True)
            hit = True
    return (ref, d, hit)


def delete_models(cache_root, specs, workers):
    if not specs:
        return 0
    total = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(_delete_one, cache_root, s): s for s in specs}
        for fut in as_completed(futs):
            ref, d, hit = fut.result()
            if hit:
                total += 1
            else:
                log("no cache dir for", ref, "(nothing to delete)")
    return total


def _download_file(job, limiter, headers, base_host):
    """job = (url, dest, rel, part). Returns (rel, bytes)."""
    url, dest, rel, part = job
    got = 0
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if os.path.exists(part):
        os.remove(part)
    import httpx
    with httpx.stream("GET", url, headers=headers, follow_redirects=True, timeout=600) as r:
        r.raise_for_status()
        with open(part, "wb") as fh:
            for chunk in r.iter_bytes(chunk_size=1 << 20):
                if limiter:
                    limiter.wait(len(chunk))
                fh.write(chunk)
                got += len(chunk)
    os.replace(part, dest)
    return (rel, got)


def pull_models(cache_root, specs, token, rate, endpoint, file_workers, repo_workers):
    import httpx  # noqa: F401
    from huggingface_hub import HfApi

    api = HfApi(token=token, endpoint=endpoint)
    limiter = RateLimiter(rate) if rate > 0 else None
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    base_host = (endpoint or "https://huggingface.co").rstrip("/")

    jobs = []  # (url, dest, rel, part)
    refs = {}  # dname -> resolved rev (for refs/main after)

    def resolve(repo, rev, includes=()):
        log("resolving", repo, rev or "(default)",
            f"[include filter: {len(includes)} pattern(s)]" if includes else "")
        info = api.model_info(repo_id=repo, revision=rev or None, files_metadata=True)
        resolved = rev or info.sha
        dname = "models--" + repo.replace("/", "--")
        snap = os.path.join(cache_root, "hub", dname, "snapshots", resolved)
        os.makedirs(snap, exist_ok=True)
        base = f"{base_host}/{repo}/resolve/{resolved}"
        file_jobs = []
        matched = skipped = 0
        for f in info.siblings:
            rel = f.rfilename
            if includes and not any(fnmatch.fnmatch(rel, p) for p in includes):
                skipped += 1
                continue
            matched += 1
            size = getattr(f, "size", None)
            dest = os.path.join(snap, rel)
            # Skip files already present and the expected size.
            if size is not None and os.path.isfile(dest) and os.path.getsize(dest) == size:
                continue
            file_jobs.append((f"{base}/{rel}", dest, rel, dest + ".part"))
        if includes:
            log(f"include filter for {repo}@{resolved[:12]}: {matched} file(s) "
                f"matched, {skipped} skipped")
            if matched == 0:
                raise RuntimeError(
                    f"include filter matched no files for {repo}@{resolved[:12]} "
                    f"(patterns: {list(includes)}) - typo or repo drift?")
            # A partial snapshot must not be resolvable by repo id: another
            # tool resolving the repo would assume config.json etc. exist.
            # Callers reference the snapshot directory by path instead.
        else:
            refs[dname] = resolved
        return file_jobs

    # Resolve repos in parallel, then gather all file jobs.
    all_jobs = []
    with ThreadPoolExecutor(max_workers=repo_workers) as ex:
        futs = {}
        for spec in specs:
            repo, rev, includes = parse_spec(spec)
            futs[ex.submit(resolve, repo, rev, tuple(includes))] = (repo, rev)
        for fut in as_completed(futs):
            repo, rev = futs[fut]
            fjobs = fut.result()
            log("queued", len(fjobs), "file job(s) for", repo, "@", rev or "")
            all_jobs.extend(fjobs)

    # Download all files in parallel; the shared limiter caps aggregate rate.
    done = 0
    total_bytes = 0
    with ThreadPoolExecutor(max_workers=file_workers) as ex:
        futs = {ex.submit(_download_file, j, limiter, headers, base_host): j for j in all_jobs}
        for fut in as_completed(futs):
            rel, got = fut.result()
            done += 1
            total_bytes += got
            if done % 10 == 0 or got == 0:
                log(f"  {done}/{len(all_jobs)} files, {total_bytes/1e6:.1f} MB "
                    + ("(rate-limited)" if limiter else ""))

    # Write refs/main per repo (full pulls only — see resolve()) so vllm /
    # start.sh resolution works.
    for dname, resolved in refs.items():
        refsdir = os.path.join(cache_root, "hub", dname, "refs")
        os.makedirs(refsdir, exist_ok=True)
        with open(os.path.join(refsdir, "main"), "w") as fh:
            fh.write(resolved)

    log(f"pulled {len(specs)} repo(s): {done} files, {total_bytes/1e6:.1f} MB")
    return total_bytes


def main():
    cache_root = os.environ.get("HF_HOME", "/models/.cache/huggingface")
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    token = os.environ.get("HF_TOKEN")
    endpoint = os.environ.get("HF_ENDPOINT")
    rate = env_int("RATE", DEFAULT_RATE)
    file_workers = env_int("MAX_FILE_WORKERS", 8)
    repo_workers = env_int("MAX_REPO_WORKERS", 2)
    del_workers = env_int("MAX_DELETE_WORKERS", 4)

    pull = [s.strip() for s in os.environ.get("PULL_MODELS", "").split(",") if s.strip()]
    delete = [s.strip() for s in os.environ.get("DELETE_MODELS", "").split(",") if s.strip()]

    log("cache_root=", cache_root, "rate=", rate,
        "file_workers=", file_workers, "repo_workers=", repo_workers,
        "del_workers=", del_workers)
    log("PULL:", pull)
    log("DELETE:", delete)

    if delete:
        delete_models(cache_root, delete, del_workers)
    if pull:
        pull_models(cache_root, pull, token, rate, endpoint, file_workers, repo_workers)
    if not pull and not delete:
        log("nothing to do (set PULL_MODELS and/or DELETE_MODELS)")
        sys.exit(2)

    log("done")


if __name__ == "__main__":
    main()
