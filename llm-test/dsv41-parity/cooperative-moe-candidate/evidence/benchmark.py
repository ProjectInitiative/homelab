#!/usr/bin/env python3
"""Run the exact bounded DSV41 C1/C2 streaming serving protocol."""

import argparse
import concurrent.futures
import importlib.util
import json
import statistics
import sys
import threading
import time
from pathlib import Path

COMMON = Path(__file__).resolve().parents[3] / "glm53-parity/test-continuous-batching.py"
MODEL = "DeepSeek-v4.1-Flash-EXL3"
PROMPT = (
    "Write a detailed step-by-step explanation of how a hash map works, including "
    "collision handling, resizing, and time complexity. Be thorough."
)
SEEDS = (11, 23, 47)


def load_common():
    spec = importlib.util.spec_from_file_location("dsv41_bench_common", COMMON)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load benchmark helper: {COMMON}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, help="profile label recorded in the summary")
    parser.add_argument("--url", required=True, help="OpenAI-compatible server base URL")
    parser.add_argument("--output", required=True, type=Path, help="new JSONL evidence file")
    args = parser.parse_args()
    if args.output.exists():
        parser.error(f"refusing to overwrite {args.output}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    common = load_common()

    with args.output.open("x", encoding="utf-8") as output:
        def emit(record):
            line = json.dumps(record, separators=(",", ":"))
            print(line, flush=True)
            output.write(line + "\n")
            output.flush()

        def one(name, prompt, max_tokens=400, seed=11, barrier=None, origin=None):
            # stream_chat fixes temperature=0/top_p=1. The seed suffix prevents
            # cross-repetition prefix reuse; it is also retained in each result.
            if barrier:
                barrier.wait()
            start = time.perf_counter() if origin is None else origin
            result = common.stream_chat(
                name=name,
                url=args.url,
                model=MODEL,
                prompt=prompt,
                max_tokens=max_tokens,
                api_key=None,
                benchmark_start=start,
                timeout=900,
                temperature=0,
                enable_thinking=False,
            )
            data = result.__dict__.copy()
            data["seed"] = seed
            return data

        warmup = one("warmup", "Explain why durable transactions need a commit record.", 32)
        emit({"kind": "warmup", "result": warmup})
        records = []
        for repetition, seed in enumerate(SEEDS, 1):
            c1 = one(f"c1-r{repetition}", PROMPT + f" [run {seed}]", 400, seed)
            record = {
                "kind": "c1", "rep": repetition, "seed": seed,
                "result": c1, "aggregate_tps": c1["decode_tok_s"],
            }
            records.append(record)
            emit(record)

            barrier = threading.Barrier(2)
            started = time.perf_counter()
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                futures = [
                    executor.submit(
                        one, f"c2-r{repetition}-s{stream}",
                        PROMPT + f" (stream {stream}/2) [run {seed}]",
                        400, seed, barrier, started,
                    )
                    for stream in (1, 2)
                ]
                results = [future.result() for future in futures]
            first_token = min(r["started_s"] + r["ttft_s"] for r in results)
            last_token = max(r["started_s"] + r["wall_s"] for r in results)
            window = last_token - first_token
            aggregate = sum(r["completion_tokens"] - 1 for r in results) / window
            record = {
                "kind": "c2", "rep": repetition, "seed": seed,
                "results": results, "aggregate_tps": aggregate, "window_s": window,
            }
            records.append(record)
            emit(record)

        summary = {}
        for kind in ("c1", "c2"):
            values = [r["aggregate_tps"] for r in records if r["kind"] == kind]
            summary[kind] = {
                "values": values, "median": statistics.median(values),
                "min": min(values), "max": max(values),
            }
        emit({"kind": "summary", "profile": args.profile, "summary": summary})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
