#!/usr/bin/env python3
"""Benchmark multiple complex OpenAI chat streams launched at the same instant.

Each request reports server-counted prompt/completion tokens, client-observed
TTFT, effective prefill rate (prompt tokens / TTFT), decode-only rate, delivered
output rate, and wall time. The aggregate uses one shared wall-clock window;
summing per-stream rates is shown only as a diagnostic and is not presented as
hardware throughput.

Prometheus counters cover the whole endpoint. Run without unrelated traffic for
an isolated server-side cross-check.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import importlib.util
import json
import os
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Any


COMPLEX_TASKS = [
    (
        "Implement a production-quality Python 3.12 asynchronous worker pool with "
        "bounded concurrency, graceful shutdown, cancellation safety, typed results, "
        "structured errors, metrics hooks, usage examples, and tests. Explain the "
        "important concurrency invariants."
    ),
    (
        "Implement a concurrency-safe generic LRU cache in Go with O(1) get/put, TTL "
        "expiration, statistics, background cleanup, configurable capacity, complete "
        "table-driven tests, and an explanation of synchronization choices."
    ),
    (
        "Design a robust PostgreSQL serializable-transaction retry helper in TypeScript "
        "with exponential backoff and jitter, AbortSignal support, SQLSTATE error "
        "classification, observability hooks, complete types, examples, and tests."
    ),
    (
        "Implement a Rust service that consumes an ordered event stream and maintains "
        "exactly-once materialized state. Cover idempotency, checkpoints, crash recovery, "
        "backpressure, graceful shutdown, property tests, and operational telemetry."
    ),
]


def load_common():
    path = Path(__file__).with_name("test-continuous-batching.py")
    spec = importlib.util.spec_from_file_location("glm53_continuous_batching", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not import {path}")
    module = importlib.util.module_from_spec(spec)
    # dataclasses resolves postponed annotations through sys.modules.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def build_prompt(task: str, request_number: int, approximate_tokens: int, nonce: str) -> str:
    """Build unique pseudo-repository context followed by a complex task."""
    target_chars = max(1, approximate_tokens) * 4
    prefix = (
        f"Concurrent benchmark request {request_number}; nonce={nonce}.\n"
        "Treat the following records as repository context. Refer to relevant components "
        "when solving the task, but do not merely summarize the records.\n"
    )
    parts = [prefix]
    length = len(prefix)
    index = 0
    while length < target_chars:
        record = (
            f"src/component_{request_number}_{index}.module: service=svc-"
            f"{(index * 17 + request_number) % 997}; dependency=dep-"
            f"{(index * 31 + 11) % 4093}; invariant=ordered-{index % 19}; "
            f"failure=retryable-{index % 7}; owner=team-{index % 13}.\n"
        )
        parts.append(record)
        length += len(record)
        index += 1
    parts.extend(["\nTask:\n", task, "\nProvide a complete, detailed answer."])
    return "".join(parts)


def delta(after: dict[str, float], before: dict[str, float], metric: str) -> float:
    return max(0.0, after.get(metric, 0.0) - before.get(metric, 0.0))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Launch complex prompts simultaneously and measure each stream."
    )
    parser.add_argument("--url", default="http://ai.taildeab2.ts.net")
    parser.add_argument("--model", default="GLM-5.3-Flash-EXL3")
    parser.add_argument("--requests", type=int, default=4)
    parser.add_argument(
        "--prompt-tokens",
        type=int,
        default=30_000,
        help="Approximate context tokens per request; server usage is authoritative",
    )
    parser.add_argument("--max-tokens", type=int, default=600)
    parser.add_argument("--temperature", type=float, default=0)
    parser.add_argument(
        "--thinking",
        action="store_true",
        help="Enable model thinking; default is disabled for reproducible decode measurement",
    )
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--timeout", type=float, default=1800.0)
    parser.add_argument(
        "--prompts-json",
        type=Path,
        help="Optional JSON array of task strings; --requests selects how many",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if args.requests < 1 or args.prompt_tokens < 1 or args.max_tokens < 1:
        parser.error("--requests, --prompt-tokens, and --max-tokens must be positive")

    common = load_common()
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("VLLM_API_KEY")
    with common.request(args.url, "/health", api_key=api_key, timeout=10.0) as response:
        if response.status != 200:
            raise RuntimeError(f"health returned HTTP {response.status}")

    if args.prompts_json:
        tasks: list[Any] = json.loads(args.prompts_json.read_text())
        if not tasks or not all(isinstance(item, str) for item in tasks):
            parser.error("--prompts-json must contain a non-empty JSON array of strings")
    else:
        tasks = COMPLEX_TASKS

    nonce = uuid.uuid4().hex
    prompts = [
        build_prompt(tasks[index % len(tasks)], index + 1, args.prompt_tokens, nonce)
        for index in range(args.requests)
    ]

    # Every worker blocks here so request start times share the same release point.
    barrier = threading.Barrier(args.requests + 1)
    benchmark_start = time.perf_counter()

    def run(index: int):
        barrier.wait()
        return common.stream_chat(
            name=f"request-{index + 1}",
            url=args.url,
            model=args.model,
            prompt=prompts[index],
            max_tokens=args.max_tokens,
            api_key=api_key,
            benchmark_start=benchmark_start,
            timeout=args.timeout,
            temperature=args.temperature,
            enable_thinking=args.thinking,
        )

    baseline = common.metric_snapshot(args.url, api_key)
    samples: list[dict[str, float]] = []
    print(
        " elapsed  done  run wait  cap defer    KV%   prompt/s      gen/s  "
        "prompt_delta gen_delta",
        flush=True,
    )

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.requests) as executor:
        futures = [executor.submit(run, index) for index in range(args.requests)]
        release_at = time.perf_counter()
        barrier.wait()
        previous = baseline
        previous_at = release_at
        while not all(future.done() for future in futures):
            time.sleep(args.interval)
            now = time.perf_counter()
            current = common.metric_snapshot(args.url, api_key)
            elapsed = max(now - previous_at, 1e-9)
            prompt_delta = delta(current, previous, "vllm:prompt_tokens_total")
            generation_delta = delta(current, previous, "vllm:generation_tokens_total")
            row = {
                "elapsed_s": now - release_at,
                "completed": sum(future.done() for future in futures),
                "running": current.get("vllm:num_requests_running", 0.0),
                "waiting": current.get("vllm:num_requests_waiting", 0.0),
                "waiting_capacity": current.get("bench:waiting_capacity", 0.0),
                "waiting_deferred": current.get("bench:waiting_deferred", 0.0),
                "kv_pct": 100 * current.get("vllm:kv_cache_usage_perc", 0.0),
                "prompt_delta": prompt_delta,
                "generation_delta": generation_delta,
                "prompt_tok_s": prompt_delta / elapsed,
                "generation_tok_s": generation_delta / elapsed,
            }
            samples.append(row)
            print(
                f"{row['elapsed_s']:8.1f} {row['completed']:5.0f} "
                f"{row['running']:4.0f} {row['waiting']:4.0f} "
                f"{row['waiting_capacity']:4.0f} {row['waiting_deferred']:5.0f} "
                f"{row['kv_pct']:6.1f} {row['prompt_tok_s']:10.1f} "
                f"{row['generation_tok_s']:10.1f} {prompt_delta:12.0f} "
                f"{generation_delta:9.0f}",
                flush=True,
            )
            previous, previous_at = current, now

        results = [future.result() for future in futures]
        finished_at = time.perf_counter()
        final_metrics = common.metric_snapshot(args.url, api_key)

    print("\nPer-request results:")
    for result in results:
        pp = result.effective_prefill_tok_s
        decode = result.decode_tok_s
        delivered = result.delivered_completion_tok_s
        print(
            f"{result.name}: ok={result.ok} prompt={result.prompt_tokens} "
            f"completion={result.completion_tokens} TTFT={result.ttft_s:.3f}s "
            f"effective-PP={pp:.1f} tok/s decode={decode:.1f} tok/s "
            f"wall={result.wall_s:.3f}s delivered={delivered:.1f} tok/s"
            if result.ttft_s is not None and pp is not None and decode is not None
            and delivered is not None
            else f"{result.name}: {result}"
        )

    benchmark_wall_s = finished_at - release_at
    total_prompt_tokens = sum(result.prompt_tokens for result in results)
    total_completion_tokens = sum(result.completion_tokens for result in results)
    earliest_first = min(
        result.started_s + (result.ttft_s or result.wall_s) for result in results
    )
    latest_finish = max(result.started_s + result.wall_s for result in results)
    shared_decode_window_s = max(latest_finish - earliest_first, 1e-9)
    decode_tokens = sum(max(result.completion_tokens - 1, 0) for result in results)

    server_draft_steps = delta(
        final_metrics, baseline, "vllm:spec_decode_num_drafts_total"
    )
    server_draft_tokens = delta(
        final_metrics, baseline, "vllm:spec_decode_num_draft_tokens_total"
    )
    server_accepted_tokens = delta(
        final_metrics, baseline, "vllm:spec_decode_num_accepted_tokens_total"
    )
    summary = {
        "requests": args.requests,
        "all_requests_ok": all(result.ok for result in results),
        "benchmark_wall_s": benchmark_wall_s,
        "total_prompt_tokens": total_prompt_tokens,
        "total_completion_tokens": total_completion_tokens,
        "total_tokens": total_prompt_tokens + total_completion_tokens,
        "aggregate_effective_prefill_tok_s": total_prompt_tokens
        / max((result.ttft_s or result.wall_s) for result in results),
        "aggregate_decode_tok_s_shared_window": decode_tokens / shared_decode_window_s,
        "aggregate_delivered_completion_tok_s": total_completion_tokens
        / benchmark_wall_s,
        "aggregate_all_tokens_tok_s": (total_prompt_tokens + total_completion_tokens)
        / benchmark_wall_s,
        "sum_individual_effective_prefill_tok_s_diagnostic": sum(
            result.effective_prefill_tok_s or 0.0 for result in results
        ),
        "sum_individual_decode_tok_s_diagnostic": sum(
            result.decode_tok_s or 0.0 for result in results
        ),
        "server_prompt_tokens_delta": delta(
            final_metrics, baseline, "vllm:prompt_tokens_total"
        ),
        "server_generation_tokens_delta": delta(
            final_metrics, baseline, "vllm:generation_tokens_total"
        ),
        "server_speculative_draft_steps": server_draft_steps,
        "server_speculative_draft_tokens": server_draft_tokens,
        "server_speculative_accepted_tokens": server_accepted_tokens,
        "server_speculative_acceptance_pct": (
            100 * server_accepted_tokens / server_draft_tokens
            if server_draft_tokens
            else None
        ),
        "server_speculative_accepted_per_step": (
            server_accepted_tokens / server_draft_steps if server_draft_steps else None
        ),
        "max_running": max((sample["running"] for sample in samples), default=0),
        "max_waiting": max((sample["waiting"] for sample in samples), default=0),
        "max_waiting_capacity": max(
            (sample["waiting_capacity"] for sample in samples), default=0
        ),
        "max_waiting_deferred": max(
            (sample["waiting_deferred"] for sample in samples), default=0
        ),
        "peak_kv_pct": max((sample["kv_pct"] for sample in samples), default=0),
    }
    report = {
        "url": args.url,
        "model": args.model,
        "configuration": vars(args)
        | {
            "prompts_json": str(args.prompts_json) if args.prompts_json else None,
            "output": str(args.output) if args.output else None,
        },
        "summary": summary,
        "results": [common.asdict(result) for result in results],
        "samples": samples,
    }
    print("\nAggregate summary:")
    print(json.dumps(summary, indent=2))
    if args.output:
        args.output.write_text(json.dumps(report, indent=2) + "\n")
        print(f"Full report: {args.output}")

    return 0 if summary["all_requests_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
