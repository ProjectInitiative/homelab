#!/usr/bin/env python3
"""Generic Hugging Face cache puller/deleter for the shared model volume.

Model-agnostic: declare repos to pull and/or delete as parameters. Downloads are
streamed by this script and rate-limited *in code* (a single token bucket shared
across all files), so a large preload caps at RATE bytes/sec and leaves the rest
of the site's bandwidth for work / household. No tc or iproute2 needed.

Parameters (env):
  HF_HOME            required   HF cache root (default /models/.cache/huggingface)
  PULL_MODELS        optional   comma-separated 'repo@revision' entries (revision optional)
  DELETE_MODELS      optional   comma-separated HF repo ids (or bare cache dirs like models--org--name)
  RATE               optional   max bytes/sec across all pulls (default 104857600 = 100 MiB/s; 0 = unlimited)
  HF_TOKEN           optional   token for gated / rate-limited repos
  HF_ENDPOINT        optional   override the Hugging Face endpoint
"""
import os
import sys
import time
import shutil

DEFAULT_RATE = 104857600  # 100 MiB/s


def log(*a):
    print("[puller]", *a, flush=True)


def cache_dirname(ref):
    if "/" in ref:
        return "models--" + ref.replace("/", "--")
    return ref


class RateLimiter:
    """Single token bucket shared across every file in the run."""

    def __init__(self, rate):
        self.rate = float(rate)
        self.credits = self.rate
        self.last = time.monotonic()

    def wait(self, n):
        now = time.monotonic()
        self.credits = min(self.rate, self.credits + (now - self.last) * self.rate)
        self.last = now
        if self.credits < n:
            time.sleep((n - self.credits) / self.rate)
            self.credits = 0.0
        else:
            self.credits -= n


def delete_models(cache_root, specs):
    total = 0
    for ref in specs:
        d = cache_dirname(ref)
        hit = False
        for base in (os.path.join(cache_root, "hub"), cache_root):
            p = os.path.join(base, d)
            if os.path.isdir(p):
                log("deleting", p)
                shutil.rmtree(p, ignore_errors=True)
                total += 1
                hit = True
        if not hit:
            log("no cache dir for", ref, "(nothing to delete)")
    return total


def pull_models(cache_root, specs, token, rate, endpoint):
    import httpx
    from huggingface_hub import HfApi

    api = HfApi(token=token, endpoint=endpoint)
    limiter = RateLimiter(rate) if rate > 0 else None
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    base_host = "https://huggingface.co"
    if endpoint:
        base_host = endpoint.rstrip("/")

    total_bytes = 0
    for spec in specs:
        repo, rev = (spec.rsplit("@", 1) if "@" in spec else (spec, None))
        log("resolving", repo, rev or "(default)")
        info = api.model_info(repo_id=repo, revision=rev or None, files_metadata=True)
        resolved = rev or info.sha
        dname = "models--" + repo.replace("/", "--")
        snap = os.path.join(cache_root, "hub", dname, "snapshots", resolved)
        os.makedirs(snap, exist_ok=True)
        base = f"{base_host}/{repo}/resolve/{resolved}"
        n_files = 0
        for f in info.siblings:
            rel = f.rfilename
            size = getattr(f, "size", None)
            dest = os.path.join(snap, rel)
            # Skip files that are already present and the expected size.
            if size is not None and os.path.isfile(dest) and os.path.getsize(dest) == size:
                n_files += 1
                continue
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            part = dest + ".part"
            if os.path.exists(part):
                os.remove(part)
            url = f"{base}/{rel}"
            got = 0
            with httpx.stream("GET", url, headers=headers, follow_redirects=True, timeout=600) as r:
                r.raise_for_status()
                with open(part, "wb") as fh:
                    for chunk in r.iter_bytes(chunk_size=1 << 20):
                        if limiter:
                            limiter.wait(len(chunk))
                        fh.write(chunk)
                        got += len(chunk)
            os.replace(part, dest)
            total_bytes += got
            n_files += 1
            log(f"  {rel} -> {got} bytes" + (" (rate-limited)" if limiter else ""))
        # Write refs/main so the parity serve / vllm resolution finds the snapshot.
        refsdir = os.path.join(cache_root, "hub", dname, "refs")
        os.makedirs(refsdir, exist_ok=True)
        with open(os.path.join(refsdir, "main"), "w") as fh:
            fh.write(resolved)
        log(f"complete {repo}@{resolved}: {n_files} files, {total_bytes} bytes total")

    return total_bytes


def main():
    cache_root = os.environ.get("HF_HOME", "/models/.cache/huggingface")
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    token = os.environ.get("HF_TOKEN")
    endpoint = os.environ.get("HF_ENDPOINT")
    rate = int(os.environ.get("RATE", DEFAULT_RATE))

    pull = [s.strip() for s in os.environ.get("PULL_MODELS", "").split(",") if s.strip()]
    delete = [s.strip() for s in os.environ.get("DELETE_MODELS", "").split(",") if s.strip()]

    log("cache_root=", cache_root, "rate=", rate)
    log("PULL:", pull)
    log("DELETE:", delete)

    if delete:
        delete_models(cache_root, delete)
    if pull:
        pull_models(cache_root, pull, token, rate, endpoint)
    if not pull and not delete:
        log("nothing to do (set PULL_MODELS and/or DELETE_MODELS)")
        sys.exit(2)

    log("done")


if __name__ == "__main__":
    main()
