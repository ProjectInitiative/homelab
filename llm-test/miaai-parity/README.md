# MiaAI DeepSeek Vision-Exp parity lane

This directory is the active MiaAI lane. Do not apply files under `../archive/legacy/`.

## Files

- `12-miaai-assets.yaml`: complete MiaAI profile, patch tree, and runtime assets.
- `12-deepseek-miaai-parity.yaml`: parity Deployments, init containers, and upstream vLLM command. Deployments intentionally default to `replicas: 0`.
- `services.yaml`: internal parity Services, a pod-network HAProxy relay, and the Tailscale Service `ai` (`ai.taildeab2.ts.net:80` → relay → vLLM port 8000).
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

# Optional cleanup of old diagnostic Services. Do not delete `ai` unless intentionally
# removing the Tailscale endpoint; the next apply recreates/configures it.
kubectl delete service deepseek deepseek-worker -n llm-test --ignore-not-found

# Install the complete MiaAI ConfigMaps/assets first.
kubectl apply --server-side -f llm-test/miaai-parity/12-miaai-assets.yaml

# Create parity resources. Deployments remain at zero after this step.
kubectl apply --server-side -f llm-test/miaai-parity/12-deepseek-miaai-parity.yaml

# Start worker first, then head.
kubectl scale deployment deepseek-parity-worker -n llm-test --replicas=1
kubectl wait --for=condition=Ready pod -l app=deepseek-parity-worker \
  -n llm-test --timeout=180s

kubectl scale deployment deepseek-parity-head -n llm-test --replicas=1
kubectl wait --for=condition=Ready pod -l app=deepseek-parity-head \
  -n llm-test --timeout=180s

# Create the internal Services and optional Tailscale API endpoint.
kubectl apply --server-side -f llm-test/miaai-parity/services.yaml
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

The shared `ai` endpoint is served by a LiteLLM-compatible gateway. It exposes the active DGX backend as `dgx-spark` and the Strix Halo backend as `qwen3.8-flash-next-halogen`, routing by the requested OpenAI `model` field. The DGX target remains the host-network API at `172.16.4.55:8000`; Halogen is reached through its normal Kubernetes Service. Background backend health checks remove failed deployments from routing.
