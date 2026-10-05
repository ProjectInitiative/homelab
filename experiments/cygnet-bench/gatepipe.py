#!/usr/bin/env python3
"""gatepipe — pluggable layered content gate over a System One classifier.

DESIGN (see README-gatepipe.md):
  Layer 0  deterministic regex (structural credentials)   ~microseconds
  Layer 1+ System One questions, ALL fired concurrently   ~120-250ms warm
           (secrets, injection, PII, project-mentions, ...)

Layers are declared, not coded: a layer is either a regex pack (layer 0)
or a question preset (System One). Adding "flag mentions of Project X"
is a config entry + a preset file. Verdicts combine per-layer policy:
  any            — any layer flagging trips the gate (secrets posture)
  all            — every layer must flag (narrow semantics)
  weighted       — named layers with weights, score >= threshold
Short-circuit: layer 0 hard-hits can skip the LLM layers entirely
(configurable — regex hits alone are usually reason enough to block).

Performance notes:
  - one chunk -> N questions = N concurrent HTTP calls; vLLM batches them
    server-side, marginal cost per extra question is small (measured:
    secrets+injection dual ran at roughly single-question wall time)
  - per-question results are cached by (question_id, sha256(chunk))
  - layer failures are fail-closed or fail-open per layer policy

Usage:
    from gatepipe import Gate, RegexLayer, SystemOneLayer, LoadError
    gate = Gate.from_config("gatepipe.yaml", endpoint=BASE)
    verdict = gate.inspect("some text to gate")
    verdict.blocked, verdict.layer_results, verdict.latency_ms
"""
from __future__ import annotations

import concurrent.futures as cf
import dataclasses
import hashlib
import json
import pathlib
import time
import urllib.request
from typing import Any, Callable

import yaml

from sec_scan import scan as regex_scan


# ----------------------------------------------------------------- layers --
@dataclasses.dataclass
class LayerResult:
    layer: str
    kind: str            # "regex" | "systemone"
    flagged: bool | None # None = layer errored
    detail: dict
    ms: float


@dataclasses.dataclass
class Verdict:
    blocked: bool
    text_sha256: str
    layer_results: list[LayerResult]
    latency_ms: float
    errors: list[str]

    def to_dict(self) -> dict:
        d = dataclasses.asdict(self)
        return d


class RegexLayer:
    """Layer 0: deterministic scan (sec_scan.py patterns + allowlists)."""

    def __init__(self, name: str = "regex", short_circuit: bool = True):
        self.name = name
        self.short_circuit = short_circuit

    def check(self, text: str) -> LayerResult:
        t0 = time.time()
        try:
            s = regex_scan(text)
            return LayerResult(self.name, "regex", s["flag"],
                               {"n_real": s["n_real"],
                                "hits": [h["pattern"] for h in s["hits"] if not h["allowlisted"]]},
                               (time.time() - t0) * 1000)
        except Exception as e:
            return LayerResult(self.name, "regex", None, {"error": repr(e)[:120]},
                               (time.time() - t0) * 1000)


class SystemOneLayer:
    """Layer 1+: one question preset against a /v1/systemone endpoint.

    endpoint is callable(text) -> float in [0,1] (P(yes)); tests can pass
    a stub. Production passes an HTTP transport (see http_transport).
    """

    def __init__(self, name: str, question: dict, endpoint: Callable[[str], float],
                 threshold: float = 0.5, on_error: str = "closed"):
        self.name = name
        self.question = question
        self.endpoint = endpoint
        self.threshold = threshold
        self.on_error = on_error   # closed -> errors flag; open -> errors pass
        self._cache: dict[tuple[str, str], float] = {}

    def check(self, text: str) -> LayerResult:
        t0 = time.time()
        key = (self.name, hashlib.sha256(text.encode()).hexdigest())
        try:
            p = self._cache.get(key)
            cached = p is not None
            if not cached:
                p = float(self.endpoint(text))
                self._cache[key] = p
            return LayerResult(self.name, "systemone", p >= self.threshold,
                               {"p": round(p, 4), "cached": cached},
                               (time.time() - t0) * 1000)
        except Exception as e:
            flagged = None if self.on_error == "open" else True
            return LayerResult(self.name, "systemone", flagged,
                               {"error": repr(e)[:120]}, (time.time() - t0) * 1000)


def http_transport(endpoint_url: str, timeout: float = 30.0):
    """Transport factory for production use.

    Returns make(question) -> callable(text) -> P(true). Each System One
    layer gets its own bound caller (the shim answers one question per
    call; the gate fans them out concurrently).
    """
    def make(question: dict) -> Callable[[str], float]:
        def call(text: str) -> float:
            body = json.dumps({"state": {"text": text},
                               "questions": {"decision": question}}).encode()
            req = urllib.request.Request(
                endpoint_url, data=body, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                ans = (json.loads(r.read().decode()).get("answers") or {}).get("decision") or {}
            return float(ans.get("noul", 0.0))
        return call
    return make


# ------------------------------------------------------------------- gate --
class Gate:
    def __init__(self, layers: list, combine: str = "any",
                 weights: dict[str, float] | None = None,
                 threshold: float = 0.5, regex_short_circuit: bool = True):
        self.layers = layers
        self.combine = combine
        self.weights = weights or {}
        self.threshold = threshold
        self.regex_short_circuit = regex_short_circuit

    @classmethod
    def from_config(cls, path: str | pathlib.Path, endpoint_url: str,
                    timeout: float = 30.0) -> "Gate":
        cfg = yaml.safe_load(pathlib.Path(path).read_text())
        factory = http_transport(endpoint_url, timeout)
        layers: list = []
        for l in cfg.get("layers", []):
            if not l.get("enabled", True):
                continue
            if l["type"] == "regex":
                layers.append(RegexLayer(l.get("name", "regex"),
                                         l.get("short_circuit", True)))
            elif l["type"] == "systemone":
                q = l["question"]
                layers.append(SystemOneLayer(l["name"], q, factory(q),
                                             l.get("threshold", 0.5),
                                             l.get("on_error", "closed")))
            else:
                raise ValueError(f"unknown layer type: {l['type']}")
        return cls(layers, cfg.get("combine", "any"),
                   cfg.get("weights"), cfg.get("threshold", 0.5),
                   cfg.get("regex_short_circuit", True))

    def inspect(self, text: str) -> Verdict:
        t0 = time.time()
        errors: list[str] = []
        results: list[LayerResult] = []
        regex_hit = False

        # layer 0 first (deterministic, ordered before LLM layers)
        ordered = sorted(self.layers, key=lambda l: 0 if getattr(l, "kind" if False else "name", "") and isinstance(l, RegexLayer) else 1)
        llm_layers = [l for l in ordered if isinstance(l, SystemOneLayer)]

        for l in ordered:
            if isinstance(l, RegexLayer):
                r = l.check(text)
                results.append(r)
                if r.flagged and l.short_circuit and self.regex_short_circuit:
                    regex_hit = True
                elif r.flagged:
                    regex_hit = True

        # fan out all System One layers concurrently (unless short-circuiting)
        if llm_layers and not (regex_hit and self.regex_short_circuit):
            with cf.ThreadPoolExecutor(min(len(llm_layers), 8)) as ex:
                futures = {ex.submit(l.check, text): l for l in llm_layers}
                for f in cf.as_completed(futures):
                    results.append(f.result())
        elif regex_hit and self.regex_short_circuit:
            # record skipped LLM layers as not-run
            for l in llm_layers:
                results.append(LayerResult(l.name, "systemone", None,
                                           {"skipped": "regex short-circuit"}, 0.0))

        # combine
        flagged_results = [r for r in results if r.flagged]
        if self.combine == "any":
            blocked = bool(flagged_results)
        elif self.combine == "all":
            s1 = [r for r in results if isinstance(getattr(r, "detail", None), dict) and r.kind == "systemone"]
            blocked = bool(s1) and all(r.flagged for r in s1)
        elif self.combine == "weighted":
            score = sum(self.weights.get(r.layer, 1.0) for r in flagged_results)
            blocked = score >= self.threshold
        else:
            raise ValueError(f"unknown combine: {self.combine}")

        errors = [f"{r.layer}: {r.detail.get('error')}" for r in results if r.flagged is None and r.detail.get("error")]
        lat = (time.time() - t0) * 1000
        return Verdict(blocked, hashlib.sha256(text.encode()).hexdigest()[:16],
                       results, lat, errors)


def main() -> None:
    """CLI: echo a text through the gate.  gatepipe.py gatepipe.yaml < text"""
    import sys
    cfg_path, endpoint = sys.argv[1], sys.argv[2]
    gate = Gate.from_config(cfg_path, endpoint)
    v = gate.inspect(sys.stdin.read())
    print(json.dumps(v.to_dict(), indent=1))


if __name__ == "__main__":
    main()
