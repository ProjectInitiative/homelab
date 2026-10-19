#!/usr/bin/env python3
"""Convert downloaded seed datasets (HF cache on PVC) -> DATA-SPEC row schema.

v2 mix (subsampled; synthetic 408 stays the core):
  wildguardmix train prompt-only rows  -> flag (unsafe) / pass (benign), ~2400
  walledai/XSTest                      -> pass (over-refusal negatives), 450
  deepset/prompt-injections            -> flag (injection), ~510
  nvidia Aegis 2.0                     -> flag/pass per annotation, ~1200
Output: /data/rkcls/seed-sft.jsonl (schema per DATA-SPEC.md)
"""
import glob
import json
import pathlib
import random

HF = pathlib.Path("/models-rw/.cache/huggingface")
OUT = pathlib.Path("/data/rkcls/seed-sft.jsonl")  # v4: aligned seed only, generic pass capped
SEED = 1729
rng = random.Random(SEED)

def cache_snapshots(repo_dirname):
    d = HF / repo_dirname / "snapshots"   # flat HF cache: datasets--org--name/snapshots
    if not d.exists():
        return []
    return sorted(p for p in d.iterdir() if p.is_dir())

def find_files(snap, exts):
    out = []
    for ext in exts:
        out += glob.glob(str(snap / "**" / f"*.{ext}"), recursive=True)
    return out

rows = []

def emit(source, expected, category, content):
    content = (content or "").strip()
    if not (10 < len(content) < 20000):
        return
    rows.append({
        "id": f"seed-{source}-{len(rows):06d}",
        "category": category, "expected": expected,
        "content": content, "source": "seed-v2",
        "generator": f"convert-{source}",
    })

# ---- wildguardmix: prompt-only train rows --------------------------------
# schema: {prompt, response, is_prompt_harmful, is_response_harmful, ...}
for snap in cache_snapshots("datasets--allenai--wildguardmix"):
    for f in find_files(snap, ["parquet"]):
        if "train" not in f or "test" in f:
            continue
        import pyarrow.parquet as pq
        t = pq.read_table(f).to_pylist()
        flag_pool, pass_pool = [], []
        for r in t:
            p = (r.get("prompt") or "").strip()
            if not p or (r.get("response") or ""):
                continue  # prompt-only rows only
            harmful = str(r.get("prompt_harm_label", "")).lower() == "harmful"
            (flag_pool if harmful else pass_pool).append(p)
        rng.shuffle(flag_pool); rng.shuffle(pass_pool)
        for p in pass_pool[:300]:
            emit("wildguardmix", "pass", "harm_prompt_benign", p)
        print("wildguardmix: kept", len([r for r in rows if r['generator']=='convert-wildguardmix']))
        break

# ---- XSTest: over-refusal benign negatives (capped 200, v4) ---------------
XSTEST_POOL = []
for snap in cache_snapshots("datasets--walledai--XSTest"):
    for f in find_files(snap, ["parquet", "jsonl", "csv"]):
        if f.endswith(".parquet"):
            import pyarrow.parquet as pq
            t = pq.read_table(f).to_pylist()
            for r in t:
                p = (r.get("prompt") or r.get("request") or "").strip()
                XSTEST_POOL.append(p)
        elif f.endswith(".jsonl"):
            for line in open(f):
                r = json.loads(line)
                p = (r.get("prompt") or r.get("request") or "").strip()
                XSTEST_POOL.append(p)
        break
    break
rng.shuffle(XSTEST_POOL)
for p in XSTEST_POOL[:200]:
    emit("xstest", "pass", "over_refusal_benign", p)
print("xstest:", len([r for r in rows if r['generator']=='convert-xstest']))

# ---- deepset/prompt-injections (parquet: text/label) ----------------------
for snap in cache_snapshots("datasets--deepset--prompt-injections"):
    import pyarrow.parquet as pq
    for f in find_files(snap, ["parquet"]):
        if "test" in f:
            continue
        for r in pq.read_table(f).to_pylist():
            text = (r.get("text") or r.get("prompt") or "").strip()
            label = str(r.get("label", "")).lower()
            if label in ("1", "true", "injection"):
                emit("deepset", "flag", "inj_classic", text)
            elif label in ("0", "false", "benign"):
                emit("deepset", "pass", "inj_benign", text)
        break
    break
print("deepset:", len([r for r in rows if r['generator']=='convert-deepset']))

# ---- Aegis 2.0 ------------------------------------------------------------
for snap in cache_snapshots("datasets--nvidia--Aegis-AI-Content-Safety-Dataset-2.0"):
    for f in find_files(snap, ["parquet", "jsonl", "json"]):
        if "train" not in f or "refusals" in f:
            continue
        if f.endswith(".parquet"):
            import pyarrow.parquet as pq
            data = pq.read_table(f).to_pylist()
        else:
            raw = open(f).read().strip()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:  # JSONL fallback
                data = [json.loads(l) for l in raw.splitlines() if l.strip()]
        flag_pool, pass_pool = [], []
        for r in data:
            text = (r.get("prompt") or "").strip()
            if not text:
                continue
            unsafe = str(r.get("prompt_label", "")).lower() == "unsafe"
            (flag_pool if unsafe else pass_pool).append(text)
        rng.shuffle(flag_pool); rng.shuffle(pass_pool)
        for p in pass_pool[:300]:
            emit("aegis2", "pass", "aegis_safe", p)
        break
    break
print("aegis2:", len([r for r in rows if r['generator']=='convert-aegis2']))

# dedupe by content prefix
seen, dedup = set(), []
for r in rows:
    k = r["content"][:200]
    if k in seen:
        continue
    seen.add(k)
    dedup.append(r)
rng.shuffle(dedup)
OUT.write_text("\n".join(json.dumps(r) for r in dedup) + "\n")
import collections
print("TOTAL", len(dedup), "->", OUT)
print(dict(collections.Counter((r["expected"]) for r in dedup)))
print(dict(collections.Counter((r["category"]) for r in dedup)))
