# MiaAI DeepSeek Vision-Exp parity lane

This directory is the active MiaAI lane. Do not apply files under `../archive/legacy/`.

## Files

- `12-miaai-assets.yaml`: complete MiaAI profile, patch tree, and runtime assets.
- `12-deepseek-miaai-parity.yaml`: parity Deployments, init containers, and upstream vLLM command. Deployments intentionally default to `replicas: 0`.
- `deepseek-services.yaml`: lane-local head/worker Services; apply only while activating this dormant lane.
- `services.yaml`: shared LiteLLM router plus two Tailscale endpoints: `ai` retains `mc-ingress-proxy`; `ai-direct` omits `tailscale.com/proxy-group` for the node-style endpoint. Both select the same LiteLLM pod.
- `12-miaai-profile.env`: source profile used to build the assets.
- `12-miaai-parity-diff.*`: parity comparison records.

The legacy diagnostic lane (`10-deepseek.yaml` and `11-vision-exp-patches.yaml`) is under `../archive/legacy/` and must not be applied.

## Fresh deployment

Run from the repository root:

```bash
cd /home/kylepzak/homelab

# Stop/remove both old diagnostic and existing parity workloads.
kubectl scale deployment deepseek-head deepseek-worker \
  deepseek-parity-head deepseek-parity-worker \
  -n llm-test --replicas=0
kubectl wait --for=delete pod -l 'app in (deepseek-head,deepseek-worker,deepseek-parity-head,deepseek-parity-worker)' \
  -n llm-test --timeout=180s || true

# Optional cleanup of old diagnostic/relay Services. Do not delete `ai` unless
# intentionally removing the sole Tailscale endpoint; the next apply recreates it.
kubectl delete service deepseek deepseek-worker ai-proxy ai-halogen \
  -n llm-test --ignore-not-found

# Install the complete MiaAI ConfigMaps/assets first.
kubectl apply --server-side -f llm-test/miaai-parity/12-miaai-assets.yaml

# Create parity resources and lane-local Services. Deployments remain at zero.
kubectl apply --server-side -f llm-test/miaai-parity/12-deepseek-miaai-parity.yaml
kubectl apply -f llm-test/miaai-parity/deepseek-services.yaml

# Start worker first, then head.
kubectl scale deployment deepseek-parity-worker -n llm-test --replicas=1
kubectl wait --for=condition=Ready pod -l app=deepseek-parity-worker \
  -n llm-test --timeout=180s

kubectl scale deployment deepseek-parity-head -n llm-test --replicas=1
kubectl wait --for=condition=Ready pod -l app=deepseek-parity-head \
  -n llm-test --timeout=180s

# After the GitOps CNPG database and OpenBao values are ready, project the
# LiteLLM runtime credentials and apply the router plus Alloy sidecar.
kubectl apply -f llm-test/miaai-parity/litellm-secrets.yaml
kubectl get vaultstaticsecret litellm-database -n llm-test
kubectl apply -f llm-test/miaai-parity/services.yaml
```

## Verify

```bash
kubectl get pods,svc -n llm-test -o wide
kubectl get svc ai -n llm-test -o wide
kubectl logs -n llm-test deploy/deepseek-parity-head -c vllm --tail=100
kubectl logs -n llm-test deploy/deepseek-parity-worker -c vllm --tail=100
```

The primary ingress-proxy endpoint remains `http://ai.taildeab2.ts.net/`. The optional direct node-style endpoint is `http://ai-direct.taildeab2.ts.net/`; both expose port 80 and target LiteLLM's port 8000.

From a Tailscale-connected client:

```bash
curl -i http://ai.taildeab2.ts.net/health
curl http://ai.taildeab2.ts.net/v1/models
```

The shared `ai` endpoint is served by LiteLLM. It exposes the active DGX backend as `dgx-spark` and the Strix Halo backend as `qwen3.8-flash-next-halogen`, routing by the requested OpenAI `model` field. Both backends are reached through normal Kubernetes Services (`glm53-head` and `qwen38-halogen-astrolabe`). Background backend health checks remove failed deployments from routing.

## LiteLLM usage database and metrics (experimental/manual runtime)

Only the database objects are GitOps-managed: `bootstrap/base/cnpg/database/litellm-role.yaml` and `litellm-database.yaml` extend the existing three-instance `postgres-cluster`. The Postgres app also projects only `username` and `password` from OpenBao into `postgres-db` for CNPG's `DatabaseRole`. LiteLLM, its VSO projection into `llm-test`, the Alloy sidecar, and the Grafana dashboard remain manual/experimental.

### OpenBao contract and rollout order

Before committing/syncing the Postgres app changes, create the KV-v2 record in OpenBao namespace `production`, mount `k8s`, path `litellm/postgres`, with these fields:

- `username`: `litellm_user`
- `password`: the database role password (raw value for CNPG)
- `DATABASE_URL`: `postgresql://litellm_user:<URL-encoded-password>@postgres-cluster-rw.postgres-db.svc.cluster.local:5432/litellm?sslmode=require`
- `LITELLM_SALT_KEY`: a separate long random value; keep it stable across restarts/rollbacks

Populate that record using the established secure OpenBao workflow; do not put credential values in Git or shell history. URL-encode the password in `DATABASE_URL` if it contains reserved URI characters.

CNPG gets the `username`/`password` pair through the GitOps `postgres-cluster` app. The manual `litellm-secrets.yaml` VSO resource copies only `DATABASE_URL` and `LITELLM_SALT_KEY` into `Secret/litellm-database` in `llm-test`. **OpenBao is the credential source of truth**: CNPG's role needs the password before it can create/reconcile the role; it is not necessary to read a generated password back out of PostgreSQL.

### Prometheus-only test (no database required)

The current `services.yaml` intentionally has no database URL or credential references, so the metrics path can be tested now. Applying it recreates the single LiteLLM replica and causes a brief API interruption.

```bash
kubectl apply -f llm-test/miaai-parity/services.yaml
kubectl rollout status deployment/ai-proxy -n llm-test
kubectl logs -n llm-test deploy/ai-proxy -c litellm --tail=100
kubectl logs -n llm-test deploy/ai-proxy -c alloy --tail=100

# Confirm the Alloy scrape and a per-model request counter reached Dinghy.
curl -G 'http://dinghy.taildeab2.ts.net:9090/api/v1/query' \
  --data-urlencode 'query=up{job="litellm"}'
curl -G 'http://dinghy.taildeab2.ts.net:9090/api/v1/query' \
  --data-urlencode 'query=litellm_proxy_total_requests_metric_total{job="litellm",requested_model="dgx-spark"}'
```

After a short completion through `ai`, confirm `up=1` and a request counter in Dinghy Prometheus. LiteLLM's Prometheus client exports these counters with a `_total` suffix. Import `litellm-usage-dashboard.json` into Grafana to chart the results.

### Enable database-backed history later

After the OpenBao record exists and the GitOps database/role plus VSO secret in `postgres-db` are Ready:

```bash
kubectl apply -f llm-test/miaai-parity/litellm-secrets.yaml
kubectl get vaultstaticsecret litellm-database -n llm-test
kubectl get secret litellm-database -n llm-test
```

Then add `DATABASE_URL` and `LITELLM_SALT_KEY` from `Secret/litellm-database` to the LiteLLM container environment (and configure `general_settings.database_url: os.environ/DATABASE_URL`) in `services.yaml`, apply it, and verify the readiness endpoint reports `db: connected`. Do not apply the database-enabled Deployment before that secret exists.

The current config enables spend/token/request metrics and explicitly keeps prompt/response storage disabled. Database-backed usage logs remain inactive until the later DB step. The metrics callback is unauthenticated because Alloy shares the proxy Pod; `/metrics` is consequently available on the existing tailnet-only `ai` and `ai-direct` endpoints. Metric labels are restricted to model/requested model/provider/status rather than user, key, email, or IP labels.

### Alloy → Dinghy Prometheus → Grafana

The Alloy sidecar scrapes `127.0.0.1:8000/metrics` and remote-writes to `http://dinghy.taildeab2.ts.net:9090/api/v1/write`. We verified this route from an in-cluster Alloy pod: Prometheus received `up{job="litellm_alloy_remote_write_smoke"}=1`. The temporary smoke pod and ConfigMap were deleted; `alloy-remote-write-smoke.yaml` is retained as a repeatable probe. Every exported series also carries a `pod` label (Downward API pod name via the Alloy `env()` function); without it, two LiteLLM pods (both replicas and/or ai-proxy-test) writing identical `job/cluster/instance` labels collide into one flapping series and inflate `increase()`/`rate()` by orders of magnitude. Never sum token counters across pods without that label.

#### Import the custom dashboard manually

1. Open Dinghy Grafana at `http://dinghy.taildeab2.ts.net:3000`.
2. Go to **Dashboards → New → Import**.
3. Upload `llm-test/miaai-parity/litellm-usage-dashboard.json` from this repository.
4. If Grafana prompts for a data source, select the provisioned Prometheus source (`prometheus_ds`) and click **Import**.

The JSON is scoped to `job="litellm", cluster="mc"`, so it won't combine other clusters. Its panels cover selected-range request/token/actual-spend totals, request rate by alias, token/actual-spend rates by alias and routed model, current in-flight requests, request rates by HTTP status, a cached-vs-fresh input-token split, and a separate would-have-spent cost stat split by routed model. The would-have-spent stat is calculated directly from token counters and per-model reference rates; it does not use or change LiteLLM's actual `litellm_spend_metric`. The live token series distinguishes `requested_model="dgx-spark"` from `model="GLM-5.3-Flash-EXL3"`; the dashboard groups both labels. Request-count metrics remain alias-based.

LiteLLM's `litellm_input_cached_tokens_metric` is derived from provider-reported `usage.prompt_tokens_details.cached_tokens`; uncached input is total input minus cached input. The GLM launcher passes `--enable-prompt-tokens-details` through `EXTRA_ARGS` on both ranks, and the LiteLLM allowlist includes the cached-token family. This is live after the documented controlled TP2 stop/start. Prometheus now has a cached-token series for Qwen, but not for `dgx-spark`. Repeated GLM smoke requests returned `usage.prompt_tokens_details.cached_tokens: 0`; vLLM logs showed aggregate prefix-cache hits in the same period, so per-request GLM cache accounting is not yet demonstrated. The dashboard split is provider-reported and should not be treated as accurate for GLM until that discrepancy is resolved. If weights are swapped behind the same upstream model name, exact weight revisions still need an explicit version label.

Prometheus retains 90 days; after the DB step, Postgres spend logs provide the durable record. Actual local-model spend remains LiteLLM's unpriced `litellm_spend_metric` (normally $0). The separate would-have-spent panel encodes hosted-API reference prices per model: `dgx-spark` uses Z.ai GLM-5.3-Flash list prices ($0.15 input / $0.03 cache-read / $0.50 output per 1M, standard price effective 2026-09-10) and `qwen3.8-flash-next-halogen` uses Alibaba Cloud Model Studio international qwen3.8-flash prices ($0.113 input / $0.014 implicit-cache read / $0.382 output per 1M). Its PromQL computes uncached input as total input minus reported cached input, applies each model's three rates, and works retroactively over the selected range. While GLM still reports 0 cached tokens per request, its hypothetical cost prices all input at the uncached rate until that discrepancy is resolved. When a vendor reprices, update the model-specific constants in `litellm-usage-dashboard.json`; no proxy restart is needed. One $0.0000029 validation sample entered the actual spend counter during the corrected rollout, so ranges including that instant can show this tiny historical blip.

LiteLLM also maintains an [all-Prometheus-metrics dashboard](https://github.com/BerriAI/litellm/tree/main/cookbook/litellm_proxy_server/grafana_dashboard/dashboard_all_metrics) and a [compact v2 dashboard](https://github.com/BerriAI/litellm/tree/main/cookbook/litellm_proxy_server/grafana_dashboard/dashboard_v2). The all-metrics dashboard has many panels for features we have not enabled, so several would be empty here. Dinghy is Grafana 13.0.6, which also supports the [Grafana Labs LiteLLM dashboard](https://grafana.com/grafana/dashboards/24965-litellm/); our small privacy-bounded dashboard is the better fit for the four metric families currently exposed.

This does not configure LiteLLM's Admin UI/master key. UI authentication can be added separately if desired.
