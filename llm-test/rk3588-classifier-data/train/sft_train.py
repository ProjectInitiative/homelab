#!/usr/bin/env python3
"""SFT for the RK3588 edge security classifier (v1: full-parameter fine-tune
of Qwen3-0.6B on the synthetic+seed mix).

Contract (must match guard_eval.py style=finetuned):
  input  = chat-template user turn with the content to screen
  output = "flag: <category>" or "pass"   (completion-only loss)

Run on a DGX Spark (GB10): nvcr.io/nvidia/pytorch:25.11-py3 + the pinned
Arm-learning-path lib set. Weights read from the shared HF cache; artifacts
written to /data/rkcls/artifacts/.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import random

DATA = pathlib.Path("/data/rkcls")
GEN = pathlib.Path("/data/rkcls/gen")
HELDOUT_FRAC = 0.15
SEED = 1729


def load_rows() -> tuple[list[dict], list[dict]]:
    """Synthetic gen files + converted seed rows -> (train, heldout)."""
    rows: list[dict] = []
    seen_ids: set[str] = set()
    for p in sorted(GEN.glob("*.jsonl")):
        for line in p.open():
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r["id"] in seen_ids:
                continue
            seen_ids.add(r["id"])
            rows.append(r)
    if (DATA / "sft-train.jsonl").exists():
        for line in (DATA / "sft-train.jsonl").open():
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    if not rows:
        raise SystemExit(f"no training rows found under {GEN} or sft-train.jsonl")

    rng = random.Random(SEED)
    rng.shuffle(rows)
    n_hold = int(len(rows) * HELDOUT_FRAC)
    return rows[n_hold:], rows[:n_hold]


SYSTEM_PROMPT = (
    "You are a security screening gate for an AI assistant. Classify the "
    "following content. Reply with exactly one of: 'pass' (benign), "
    "'flag: secret_material', 'flag: injection', or 'flag: sensitive' "
    "followed by the category that applies."
)


def to_example(row: dict) -> dict:
    """TRL prompt-completion format; loss applies to completion only."""
    cat = row.get("category", "")
    if row["expected"] == "flag":
        # collapse synthetic categories into the 3-gate vocabulary, keep
        # the fine-grained category as a suffix comment-free token
        if "inj" in cat:
            comp = "flag: injection"
        elif any(k in cat for k in ("sensitive", "pii", "household")):
            comp = "flag: sensitive"
        else:
            comp = "flag: secret_material"
    else:
        comp = "pass"
    return {"prompt": [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": row["content"]},
    ], "completion": comp}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-model", default="Qwen/Qwen3-0.6B")
    ap.add_argument("--out", default="/data/rkcls/artifacts/rkcls-v1")
    ap.add_argument("--epochs", type=float, default=3.0)
    ap.add_argument("--lr", type=float, default=1e-5)
    ap.add_argument("--per-device-bs", type=int, default=4)
    ap.add_argument("--grad-accum", type=int, default=4)
    args = ap.parse_args()

    train_rows, hold_rows = load_rows()
    n_flag = sum(1 for r in train_rows if r["expected"] == "flag")
    print(f"train={len(train_rows)} (flag {n_flag} / pass {len(train_rows)-n_flag}), "
          f"heldout={len(hold_rows)}")

    from datasets import Dataset
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from trl import SFTConfig, SFTTrainer

    tok = AutoTokenizer.from_pretrained(args.base_model)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        args.base_model, dtype="bfloat16",
        attn_implementation="sdpa")  # flash-attn on sm_121: revisit if available

    ds = Dataset.from_list([to_example(r) for r in train_rows])

    from transformers import AutoModelForCausalLM as _AM  # noqa: F401 (already imported)
    # Render chat template ourselves: TRL 1.13 prompt-completion wants strings.
    def render(ex):
        return {
            "prompt": tok.apply_chat_template(
                ex["prompt"], tokenize=False, add_generation_prompt=True),
            "completion": ex["completion"],
        }
    ds = ds.map(render, remove_columns=[c for c in ds.column_names if c not in ("prompt", "completion")])

    cfg = SFTConfig(
        output_dir=args.out,
        num_train_epochs=args.epochs,
        learning_rate=args.lr,
        per_device_train_batch_size=args.per_device_bs,
        gradient_accumulation_steps=args.grad_accum,
        bf16=True,
        logging_steps=10,
        save_strategy="epoch",
        lr_scheduler_type="cosine",
        warmup_ratio=0.03,
        max_length=4096,
        completion_only_loss=True,
        report_to=[],
        seed=SEED,
    )
    trainer = SFTTrainer(
        model=model,
        args=cfg,
        train_dataset=ds,
        processing_class=tok,
    )
    trainer.train()
    trainer.save_model(args.out + "/final")
    tok.save_pretrained(args.out + "/final")

    (pathlib.Path(args.out) / "heldout.jsonl").write_text(
        "\n".join(json.dumps(r) for r in hold_rows) + "\n")
    print("saved", args.out + "/final")


if __name__ == "__main__":
    main()
