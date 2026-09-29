#!/usr/bin/env python3
"""Cygnet decision-model latency benchmark: NVIDIA Spark vs AMD Strix Halo.

Speaks POST /v1/systemone to the local shim. Measures:
  - cold-start (first request after pod start, includes model warm)
  - tiny canary (58 tok)   ~ agentic per-turn new-message cost
  - small (512 tok)        ~ email-classifier single email
  - large (8,192 tok)      ~ big fresh message / chunked-scan chunk batch
Reports p50/p95 per size + tokens/sec effective throughput. JSON to stdout.
"""
import json
import os
import statistics
import time

import urllib.request

ENDPOINT = os.environ.get("SHIM_URL", "http://127.0.0.1:8009/v1/systemone")

SENSITIVE_Q = {
    "decision": {
        "type": "noul",
        "instructions": (
            "Does this text contain personal, private, or sensitive information "
            "that should not be shared outside the organization?"
        ),
        "criteria": {
            "true": (
                "Yes — the text contains personal, private, or sensitive information: "
                "names, email addresses, phone numbers, physical addresses, account "
                "numbers, API keys, passwords, tokens, or credentials."
            ),
            "false": (
                "No — the text contains no personal, private, or sensitive information "
                "of any kind."
            ),
        },
    }
}

# ~58 tokens of filler prompt (mirrors the estate warmup shape)
TINY = ("Reply to the user greeting briefly. " * 4) + "The meeting is at nine, agenda attached, please review before Friday and ping jane about the venue."

# ~512 tokens: a plausible email
SMALL = """Subject: Q3 infrastructure review and migration timeline

Hi team,

Thanks for the feedback on the migration plan. I have merged the comments from
the platform review into version 4 of the doc. A few highlights and open items
below, please review before Thursday's sync.

1. The database migration window is confirmed for the second weekend of next
month. We will run the rehearsal on the staging environment starting Wednesday
night. The rehearsal includes a full restore from the latest backup and a
failover drill between regions. The on-call rotation needs one more volunteer
for the Saturday shift.

2. The object storage cutover is blocked on the network team's firewall
changes. The change request is CHG-48213 and it is in review. If it does not
land by Friday we slip the cutover by a week and notify the customers who
opted into the early window.

3. The cost report is attached. Spend on the inference cluster is up 12%
month over month, mostly from the new GPU nodes. The reserved-instance
purchase will bring it down next quarter. Finance signed off on the budget.

4. Security reminded everyone that service tokens must rotate every 90 days.
The rotation job runs weekly and posts failures to the alerts channel. Two
services are past due and their owners have been pinged twice.

Action items: review the doc, sign up for the on-call shift, and confirm your
team's migration slot by end of week.

Best,
Alex
""" * 2

# ~8,192 tokens: repeated technical content (deterministic)
BLOCK = (
    "Section {i}. The service exposes a health endpoint that returns the status of "
    "its dependencies. The database pool is sized at twenty connections per replica. "
    "The cache uses a least-recently-used policy with a ten minute TTL. Retries use "
    "exponential backoff with jitter, three attempts maximum. Logs are structured "
    "JSON shipped to the aggregator. Metrics scrape every fifteen seconds. "
)
LARGE = " ".join(BLOCK.format(i=i) for i in range(128))


def call(state: str) -> tuple[float, str]:
    body = json.dumps({
        "model": "cygnet",
        "state": state,
        "questions": SENSITIVE_Q,
    }).encode()
    req = urllib.request.Request(
        ENDPOINT, data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=600) as r:
        payload = json.loads(r.read())
    ms = (time.perf_counter() - t0) * 1000
    p = payload["answers"]["decision"]["noul"]
    return ms, p


def stats(samples):
    ss = sorted(samples)
    return {
        "n": len(ss),
        "p50_ms": round(statistics.median(ss), 1),
        "p95_ms": round(ss[max(0, int(len(ss) * 0.95) - 1)], 1),
        "min_ms": round(ss[0], 1),
        "max_ms": round(ss[-1], 1),
    }


def bench(label, text, n):
    ms, p = call(text)
    cold = ms
    samples = []
    probs = [p]
    for _ in range(n):
        ms, p = call(text)
        samples.append(ms)
        probs.append(p)
    # approx token count via words*1.3
    approx_tokens = int(len(text.split()) * 1.3)
    warm_p50 = statistics.median(samples)
    return {
        "label": label,
        "approx_tokens": approx_tokens,
        "cold_first_ms": round(cold, 1),
        "warm": stats(samples),
        "tok_per_s_warm_p50": round(approx_tokens / (warm_p50 / 1000), 1),
        "verdict_range": [min(probs), max(probs)],
    }


def main():
    out = {"endpoint": ENDPOINT, "started": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    out["warmup_tiny"] = bench("tiny-warmup", TINY, 5)
    out["small_512"] = bench("small-512", SMALL, 10)
    out["large_8k"] = bench("large-8k", LARGE, 5)
    out["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
