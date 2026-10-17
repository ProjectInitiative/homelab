# rk3588-classifier-data — training pipeline for the edge security classifier

Step 2 of keel `projects/rk3588-classifier-data` (rk3588-security-classifier):
after the falsification probes (`../guard-falsify/`) ruled out a capability
wall, this builds the fine-tuning data and the SFT job.

## Pipeline stages

1. **Synthetic generation** (subagent fanout, `gen/*.jsonl`): four workers —
   secrets-flag (120), injection-flag (120), benign-lookalike (120),
   estate-traffic (120). Each self-verifies against the regex frontline
   (`sec_scan.py`, copied here). Spec: DATA-SPEC.md.
2. **Seed download** (`seed-download.yaml`): public safety datasets to the
   model-cache PVC. Landed: NVIDIA Aegis 2.0, deepset/prompt-injections.
   Gated — need Kyle's HF org approval, then re-run:
   `allenai/wildguardmix`, `walledai/XSTest`. (AdvBench mirrors 404; low
   priority, injection diversity is covered by the subagent lane.)
3. **Assembly** (`assemble.sh`): local regex verification, upload gen/ +
   spec to PVC (`/data/rkcls/`), publish the SFT code ConfigMap.
4. **SFT** (`train/`): full-parameter fine-tune of Qwen3-0.6B via TRL on
   `nvcr.io/nvidia/pytorch:25.11-py3` (Arm DGX Spark pinned lib set:
   accelerate 1.15 / datasets 5.0.1 / transformers 4.57.1 / trl 1.13).
   Prompt-completion contract: user turn = content, completion =
   `pass` | `flag: secret_material|injection|sensitive` (loss on completion
   only). Heldout 15%. Job is `suspend: true` until data lands:
   `kubectl -n llm-test patch job rkcls-sft-v1 --type=merge -p '{"spec":{"suspend":false}}'`
5. **Post-training eval** (next): serve `rkcls-v1/final` via the same
   qwen3guard deployment pattern (`GUARD_STYLE=finetuned` in guard_eval.py)
   against cygnet's held-out 231 + the synthetic heldout slice.

## Quick start (next session)

```sh
cd ~/development/homelab/llm-test/rk3588-classifier-data
# after subagent gen files exist and verify clean:
./assemble.sh
kubectl -n llm-test patch job rkcls-sft-v1 --type=merge -p '{"spec":{"suspend":false}}'
kubectl -n llm-test logs -f job/rkcls-sft-v1
```
