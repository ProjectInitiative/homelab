#!/usr/bin/env python3
"""E2E test against the deployed cygnet-classifier Service (in-cluster DNS)."""
import json
import sys
import time
import urllib.request

BASE = "http://cygnet-classifier.llm-test.svc.cluster.local:8009"

NSENSITIVE = {
    "state": {
        "email_subject": "URGENT: wire transfer",
        "email_body": "Please confirm the account number 4433-2211 and routing 021000021 for the $5,000 wire today.",
    },
    "questions": {
        "decision": {
            "type": "noul",
            "instructions": "Does this email contain sensitive financial information?",
            "criteria": {
                "true": "Yes - contains sensitive financial details.",
                "false": "No - no sensitive financial details.",
            },
        }
    },
}

NBENIGN = {
    "state": {
        "email_subject": "Lunch tomorrow?",
        "email_body": "Hey, want to grab tacos at the food trucks around noon?",
    },
    "questions": {
        "decision": {
            "type": "noul",
            "instructions": "Does this email contain sensitive personal information?",
            "criteria": {
                "true": "Yes - contains sensitive personal details.",
                "false": "No - contains no sensitive personal details.",
            },
        }
    },
}


def post(path, payload, timeout=120):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = json.loads(r.read().decode())
    return body, (time.time() - t0) * 1000


if __name__ == "__main__":
    for name, payload in [("sensitive-email", NSENSITIVE), ("benign-email", NBENIGN)]:
        try:
            body, ms = post("/v1/systemone", payload)
            print(f"{name}: {ms:.0f}ms -> {json.dumps(body.get('answers', body))[:200]}")
        except Exception as e:
            print(f"{name}: FAILED {e}")
            sys.exit(1)
