#!/usr/bin/env python3
"""distill.py — convert gate-inspector decision-log JSONL into rkcls SFT rows.

Input: decisions.jsonl records pushed by ai-gate (post-redaction
reconstruction, no live secret material — DEC-0037 posture).

Row policy (v8):
  - kind=allow, no redact chunks  -> expected=pass, content = last user
    message text (the reconstruction; for allow it is the original).
  - kind=redact / force_local     -> SKIPPED for flag rows: the reconstruction
    has the secret replaced by the armor placeholder, and training
    "flag: <placeholder>" would teach the v6 shallow-matching trap. These
    records are counted for threshold calibration instead.
  - Sensitive-but-allow (any layer P >= 0.35) rows keep expected=pass — the
    gate already decided pass is the correct action; that is the teacher.

Usage: python3 distill.py /data/rkcls-decisions/decisions.jsonl gen/estate-distilled.jsonl [--cap 800]
"""
import argparse, json, sys

def last_user_text(messages):
    for m in reversed(messages or []):
        if m.get("role") == "user":
            c = m.get("content")
            if isinstance(c, str):
                return c
            if isinstance(c, list):  # litellm content parts
                return " ".join(p.get("text", "") for p in c if isinstance(p, dict))
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--cap", type=int, default=800)
    a = ap.parse_args()

    rows, seen, stats = [], set(), {"allow": 0, "redact": 0, "force_local": 0, "empty": 0, "dup": 0, "kept": 0}
    for line in open(a.src):
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        kind = r.get("kind")
        stats[kind] = stats.get(kind, 0) + 1
        if kind != "allow":
            continue  # redact/force_local: calibration stats only (see docstring)
        text = last_user_text(r.get("messages"))
        if not text or not text.strip():
            stats["empty"] += 1
            continue
        key = text[:256]
        if key in seen:
            stats["dup"] += 1
            continue
        seen.add(key)
        if stats["kept"] >= a.cap:
            break
        rows.append({
            "id": f"distill-{r.get('ts', 0):.0f}-{len(rows)}",
            "category": "estate_distilled",
            "expected": "pass",
            "content": text.strip(),
            "source": "estate-verdict-soak",
            "generator": "distill-v1",
        })
        stats["kept"] += 1

    with open(a.dst, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(json.dumps(stats), file=sys.stderr)
    print(f"{len(rows)} rows -> {a.dst}")

if __name__ == "__main__":
    main()
