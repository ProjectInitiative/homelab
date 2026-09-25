# MiaAI DeepSeek Vision-Exp parity lane

This directory is the active MiaAI lane. Do not apply files under `../archive/legacy/`.

## Files

- `12-miaai-assets.yaml`: complete MiaAI profile, patch tree, and runtime assets.
- `12-deepseek-miaai-parity.yaml`: parity Deployments, init containers, and upstream vLLM command. Deployments intentionally default to `replicas: 0`.
- `deepseek-services.yaml`: lane-local head/worker Services; apply only while activating this dormant lane.
- `services.yaml`: the shared LiteLLM router and sole Tailscale Service `ai`; model backends are reached through lane-local ClusterIP Services.
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

# Create the LiteLLM router and sole Tailscale API endpoint.
kubectl apply -f llm-test/miaai-parity/services.yaml
```

## Verify

```bash
kubectl get pods,svc -n llm-test -o wide
kubectl get svc ai -n llm-test -o wide
kubectl logs -n llm-test deploy/deepseek-parity-head -c vllm --tail=100
kubectl logs -n llm-test deploy/deepseek-parity-worker -c vllm --tail=100
```

The expected API endpoint is:

```text
http://ai.taildeab2.ts.net/
```

From a Tailscale-connected client:

```bash
curl -i http://ai.taildeab2.ts.net/health
curl http://ai.taildeab2.ts.net/v1/models
```

The shared `ai` endpoint is served by LiteLLM. It exposes the active DGX backend as `dgx-spark` and the Strix Halo backend as `qwen3.8-flash-next-halogen`, routing by the requested OpenAI `model` field. Both backends are reached through normal Kubernetes Services (`glm53-head` and `qwen38-halogen-astrolabe`). Background backend health checks remove failed deployments from routing.
