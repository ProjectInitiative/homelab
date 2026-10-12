# ai-gate — classifier gate in front of LiteLLM (production rollout)

Status: **staged, not applied**. All traffic already flows through `ai-proxy`
(`ai` and `ai-direct` Tailscale LBs both select `app=ai-proxy`); this adds the
layered sensitivity/secrets/injection gate *inside* the proxy request path, per
DEC-0020/0021 option A. Nothing is committed yet; review then commit.

## What is staged (uncommitted)

- `custom_guardrail/ai_gate.py` — the guardrail: regex short-circuit + three
  concurrent System One noul layers (secret-material fail-closed, prompt
  injection fail-open, sensitivity fail-closed), verdict-not-forensics.
- `../miaai-parity/services.yaml` — patched with:
  - `guardrails:` block in `ai-proxy-config` (`custom_guardrail.ai_gate.AiGate`,
    `mode: pre_call`, `default_on: true`)
  - `ai-gate-code` ConfigMap (the guardrail source)
  - `gate-code` volume/mount at `/app/custom_guardrail` + `AI_GATE_URL` /
    `AI_GATE_FAIL_MODE` env on the `litellm` container
- `canary-job.yaml` — in-cluster must-block/must-allow canary against the
  *gated* endpoint; exits nonzero on any false positive/negative.
- `cnp-model-egress.yaml` — DRAFT CiliumNetworkPolicy enforcing "model lanes are
  only reachable from ai-proxy" (apply only after the client audit).

Verified against the deployed LiteLLM build: `initialize_guardrails`,
`CustomLogger.async_pre_call_hook`, and `httpx` all present; the POC's
`launch_gate.py` workaround is not needed.

## Rollout phases

1. **Preconditions** — `cygnet-gate` has ≥1 Ready endpoint
   (`kubectl get endpointslice -n llm-test -l kubernetes.io/service-name=cygnet-gate`)
   and the canaries pass *directly* against cygnet-gate first.
2. **Canary the classifier** — run the direct-to-gate canary variant of
   `canary-job.yaml` (set `CANARY_TARGET` to the gate) to baseline recall/FPR.
3. **Apply the proxy change** — one `Recreate` rollout of `ai-proxy`:
   ```bash
   kubectl apply -n llm-test -f <(extract configmaps + deployment from services.yaml)
   kubectl rollout status deployment/ai-proxy -n llm-test --timeout=180s
   ```
   Brief `ai`/`ai-direct` outage during the Recreate swap — schedule accordingly.
4. **Canary the gated endpoint** — `kubectl apply -f canary-job.yaml`; must pass
   100% (12 block, 10+ allow, and blocked bodies must not echo flagged spans).
   Known quirk so far: bare constraint-style imperatives ("Say OK and nothing
   else.") score ~0.71 on the prompt-injection layer (threshold 0.5, fail-open)
   while other benign prompts score 0.01–0.08 — quantify in the soak, tune the
   threshold there, not by rewording prompts.
5. **Soak** — 24h with `AI_GATE_DISABLED` unset; watch `ai-gate:` log lines,
   LiteLLM 4xx rate, and p95 added latency (expect ~120–250 ms warm per prompt;
   regex hits are ~0 ms).
6. **Enforce "all traffic through the proxy"** — audit in-cluster callers of lane
   Services (anything POSTing to `:8000` heads besides ai-proxy), then apply
   `cnp-model-egress.yaml`. Decision-model traffic (cygnet-gate :8009) is
   intentionally untouched; email-classifier keeps its direct DEC-0022 path.

## Rollback

`kubectl set env deployment/ai-proxy -n llm-test AI_GATE_DISABLED=1` (break-glass,
no restart) or re-apply the pre-gate services.yaml. The gate code ConfigMap is
 inert once unmounted.

## Tuning

- Thresholds live in `custom_guardrail/ai_gate.py` (`QUESTIONS`), mirroring
  `experiments/cygnet-bench/gatepipe.yaml` (secrets 0.5, injection 0.5) plus the
  POC sensitivity 0.60. Raise if canaries/legal users see false positives.
- `AI_GATE_FAIL_MODE=closed` keeps the DEC-0020 posture: classifier down ⇒ no
  data leaves the estate.
- Add new detection goals as extra entries in `QUESTIONS` (config-not-code), the
  same way gatepipe layers are declared. **Layer activation is per-deployment**
  via `AI_GATE_LAYERS` (comma list, default `secret-material,prompt-injection`).
  The `sensitive` PII/exfiltration layer is OFF for ai-proxy-test: coding-agent
  contexts legitimately contain IPs/hostnames/system config and score ~0.8 on
  that preset — it hard-blocked every pi request (0.819 on a 37K-char system
  prompt). Enable it only for exfiltration-scanning consumers (email-classifier,
  DEC-0022) where such content is the actual signal.

## Open items

- Client audit for step 6 (known lane-Service callers besides ai-proxy: none
  found in repo manifests; verify live with Hubble/conntrack before applying).
- Gate metrics: scrape a counter from the guardrail logs into the existing
  Alloy/LiteLLM dashboard later (backlog, non-blocking).
