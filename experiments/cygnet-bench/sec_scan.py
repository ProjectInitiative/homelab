#!/usr/bin/env python3
"""Deterministic frontline secrets scanner (layer 0).

Curated high-precision regexes for known credential formats + two-tier
suppression:

- STRONG patterns (structural formats: AWS/GitHub/OpenAI/Slack keys, PEM
  blocks, JWTs, credentialed URLs) are suppressed ONLY when the matched
  span itself is a placeholder/example/redaction — surrounding context
  (comments mentioning vault, TODOs) never masks a structurally-valid key.
- WEAK patterns (generic key=value heuristics) are suppressed by context
  allowlist: env lookups, CI secretRef wiring, secret-manager mentions,
  test fixtures, documentation prose.

This is the cheap pass that runs on prompts of ANY size before the LLM
classifier layer. It never makes the final call in the layered design —
it finds candidate spans and suppresses obvious non-secrets — but the
eval scores it standalone so we know its recall/FPR trade.
"""
from __future__ import annotations

import re

# (name, regex, strength)  — strength: "strong" = structural format
PATTERNS: list[tuple[str, re.Pattern, str]] = [
    ("aws-access-key",   re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "strong"),
    ("github-pat",       re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,255}\b"), "strong"),
    ("github-fine-grained", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{22,255}\b"), "strong"),
    ("openai-key",       re.compile(r"\bsk-(proj|ant|svcacct)-[A-Za-z0-9_-]{20,}\b"), "strong"),
    ("openai-legacy",    re.compile(r"\bsk-[A-Za-z0-9]{20}T3BlbkFJ[A-Za-z0-9]{20}\b"), "strong"),
    ("slack-token",      re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b"), "strong"),
    ("google-api-key",   re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"), "strong"),
    ("stripe-live",      re.compile(r"\b(sk|pk)_live_[A-Za-z0-9]{20,}\b"), "strong"),
    ("npm-token",        re.compile(r"\bnpm_[A-Za-z0-9]{36}\b"), "strong"),
    ("pem-private-key",  re.compile(r"-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"), "strong"),
    ("jwt",              re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"), "strong"),
    ("conn-cred",        re.compile(r"\b[a-z][a-z0-9+.-]*://[^\s/:@]+:[^\s/@]+@[^\s]+"), "strong"),
    ("kv-secret",        re.compile(r"(?i)\b(secret|password|passwd|token|api[_-]?key|access[_-]?key)\b\s*[=:]\s*[\"'][^\"']{12,}[\"']"), "weak"),
]

# The matched SPAN itself is a non-material value (both tiers suppress).
_SPAN_SELF_SUPPRESS = re.compile(
    r"EXAMPLE|REDACTED|\*\*+|xxxx|sk-test|ghp_xxx|<[^>]*>|\$\{")

# Contextual allowlist — WEAK tier only.
CONTEXT_ALLOWLIST = [
    re.compile(r"\$\{\{?\s*secrets?\."),
    re.compile(r"secretKeyRef|vault|hvac|openbao|bitwarden|sops\b", re.I),
    re.compile(r"os\.environ|getenv|env_var|ENV\[|from_env|load_dotenv", re.I),
    re.compile(r"\bdummy|fake|fixture|masked", re.I),
    re.compile(r"^(#|//|\"\"\"|''')|(#\s)", re.I),
]

def scan(text: str) -> dict:
    hits = []
    for name, rx, strength in PATTERNS:
        for m in rx.finditer(text):
            line_start = text.rfind("\n", 0, m.start()) + 1
            line_end = text.find("\n", m.end())
            line = text[line_start: line_end if line_end != -1 else len(text)]
            span = m.group(0)
            if strength == "strong":
                allowlisted = bool(_SPAN_SELF_SUPPRESS.search(span))
            else:
                allowlisted = (bool(_SPAN_SELF_SUPPRESS.search(span))
                               or any(a.search(line) for a in CONTEXT_ALLOWLIST))
            hits.append({
                "pattern": name,
                "strength": strength,
                "match": span[:24] + ("…" if len(span) > 24 else ""),
                "line": line.strip()[:120],
                "allowlisted": allowlisted,
            })
    real = [h for h in hits if not h["allowlisted"]]
    return {"hits": hits, "n_real": len(real), "flag": len(real) > 0}

if __name__ == "__main__":
    import json, sys
    t = sys.stdin.read()
    print(json.dumps(scan(t), indent=2))
