# rk3588-classifier — training data spec (v1)

Owner session 2026-10-16. Everything here feeds the SFT of a small guard
model (Qwen3-0.6B class) for the ai-classifier-gate's edge lane. Target
quality bar: cygnet-level recall on secrets + injection at near-zero FPR.

## Row format (JSONL, one object per line)

```json
{"id": "syn-sec-agent-tool-001", "category": "chat_credential",
 "expected": "flag", "content": "...", "source": "synthetic-v1",
 "generator": "agent-<slug>"}
```

- `expected`: `"flag"` (real threat present) or `"pass"` (benign — this is a
  *security screening* task, not content moderation; anything that would not
  cause harm if it reached an untrusted party is `pass`)
- `category`: free-form snake_case; use the cygnet corpus vocabulary when it
  fits (chat_credential, code_hardcoded, conn_string_pasted, env_file_real,
  private_key_pem, inj_fake_assistant_turn, inj_tool_hijack,
  inj_instruction_hierarchy, inj_roleplay_jailbreak, ...) so per-category
  metrics line up with the existing eval
- `content`: the raw text as it would appear in a prompt/message
- NEVER include a real secret. Fabricated-but-realistic values only
  (`ghp_` + 36 hex chars is fine; do not copy any real token).

## Mix targets (v1, ~500-600 synthetic rows)

| lane | expected | notes |
|---|---|---|
| secret material in context | flag | agent transcripts, tool outputs, env dumps, logs, emails, PR diffs, k8s manifests — the DEC-0037 "real usable material vs reference" line |
| injection / manipulation | flag | fake assistant turns, tool-result injection, instruction hierarchy attacks, system-prompt extraction, malicious tool/MCP descriptions, prompt-injected web content |
| sensitive/PII | flag | household/topology info the estate treats as sensitive (network maps, camera layouts, personal schedules) — moderate volume |
| benign look-alikes | pass | **the hard class**: scanner code, secret-manager discussions, placeholders, redacted values, test fixtures, docs, quoted injection examples, truncated/partial tokens |
| plain estate traffic | pass | normal pi sessions, nix code, HA automations, k8s ops chatter, emails — boring on purpose |

## Labeling truth sources

1. **Regex frontline** (`experiments/cygnet-bench/sec_scan.py`) is ground
   truth for structural credential formats. Synthetic secret rows MUST trip
   it; benign rows must not (allowlist hits are OK).
2. **Teacher adjudication** (in-cluster, next step): cygnet tuned/injection
   questions score every row; disagreements vs. intended label get reviewed
   before training use.
3. cygnet's **existing 231-prompt corpus stays held-out** — never train on
   it. A random 15% slice of synthetic rows is also held out as
   `heldout-*.jsonl`.

## Public seed data (downloaded to PVC by seed-download.yaml, not yet used)

WildGuardMix train, NVIDIA Aegis 2.0, deepset/prompt-injections, XSTest
(over-refusal negatives), AdvBench. Used for the safety-replay slice and
injection diversity; converted to the same row schema by `convert_seed.py`.
