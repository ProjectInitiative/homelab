# GLM-5.3-Flash EXL3 (2x DGX Spark) — MIAI parity lane

This directory is the **GLM-5.3-Flash EXL3** parity lane, mirroring the
DeepSeek lane in `../miaai-parity/`. It is a faithful Kubernetes port of the
upstream MiaAI Lab recipe
[GLM-5.3-Flash-EXL3-2x-DGX-Sparks](https://github.com/MiaAI-Lab/GLM-5.3-Flash-EXL3-2x-DGX-Sparks)
(`start.sh`) so it can run as a self-contained, deployable workload on the same
2× NVIDIA GB10 (SM121) kit the DeepSeek lane uses.

> **PRE-DEPLOY.** The Deployments here default to `replicas: 0`. Nothing is
> started by applying these files. The model weights are **not yet downloaded**;
> you must run the download job first (see below) and only then scale up.

## Files

- `05-glm53-exl3-download.yaml` — weight puller for the EXL3 model + DFlash2 draft.
- `12-glm53-assets.yaml` — ConfigMap with the two **runtime-only** overlay patches
  (`patch_adaptive_k.py`, `patch_dense_fp8.py`) that are NOT baked into the image.
- `12-glm53-parity.yaml` — parity Deployments (`glm53-exl3-head` on chronometer,
  `glm53-exl3-worker` on sextant), `replicas: 0`.
- `services.yaml` — internal Services + HAProxy relay + Tailscale `glm` endpoint.
- `12-glm53-profile.env` — the full resolved runtime profile (documentation).
- `12-glm53-parity-diff.md` — parity comparison record.

## Key pins

| Item | Value |
|---|---|
| Upstream commit | `9348755` (MiaAI-Lab/GLM-5.3-Flash-EXL3-2x-DGX-Sparks) |
| Image (public) | `ghcr.io/miaai-lab/glm-5.3-flash-2x-dgx-sparks:exl3` |
| Image digest | `sha256:eecb36e14dc34c92d46827fde7b09f7e0bf27e27c426ece126376c02dea6cd2f` |
| Weight model | `Mia-AiLab/GLM-5.3-Flash-EXL3-TR3-4bpw` @ `25a44fdbf16862a46b7cc9921142c6c81350af2f` (~164 GiB, 120 shards) |
| Draft model | `incoai/GLM-5.3-Flash-DFlash2` (k=7) @ `dc77ff1c99eeb2df044ee3d4f0094eb033fee410` (~2.3 GiB) |
| Served model id | `GLM-5.3-Flash-EXL3` |
| API port | **8000** (GLM) vs 8000 (DeepSeek) |
| KV cache dtype | `fp8` (fp8_ds_mla) |
| Quantization | `exl3` |

## Step 1 — download the weights (required)

The previous `llm-test/20-glm.yaml` puller fetches
`LibertAIDAI/GLM-5.3-Flash-NVFP4`, which is a **different (NVFP4/Ray) variant** and
is NOT what this EXL3 lane serves. The cache-preload Job is `glm53-cache-pull`; do not scale the lane unless its
completion is confirmed and the pinned EXL3 and DFlash2 snapshot files pass the
init-container checks. A missing stale NVFP4 directory is a successful delete
no-op.

```bash
kubectl apply -f llm-test/glm53-parity/05-glm53-exl3-download.yaml
kubectl wait --for=condition=Complete job/glm53-cache-pull -n llm-test --timeout=1h
```

Verify on the shared volume (RWX JuiceFS, reachable on the nodes):

```bash
ssh chronometer 'ls /var/lib/juicefs/volume/pvc-afa2ecdd-04ae-4af9-9e08-e1ea1c6d1947-fwcslx/.cache/huggingface/ | grep -i glm53'
```

You should see `models--Mia-AiLab--GLM-5.3-Flash-EXL3-TR3-4bpw` and
`models--incoai--GLM-5.3-Flash-DFlash2`.

## Step 2 — install assets + parity resources (still replicas: 0)

```bash
kubectl apply --server-side -f llm-test/glm53-parity/12-glm53-assets.yaml
kubectl apply --server-side -f llm-test/glm53-parity/12-glm53-parity.yaml
kubectl get deploy,cm -n llm-test | grep glm53
```

## Step 3 — scale up (head rank 0 first, then worker rank 1)

vLLM multi-node uses the head (rank 0) as the coordinator; bring it up first so
the worker can rendezvous via `--master-addr 172.16.5.55:29521`.

```bash
kubectl scale deploy glm53-exl3-head -n llm-test --replicas=1
kubectl wait --for=condition=Ready pod -l app=glm53-exl3-head -n llm-test --timeout=1800s
kubectl scale deploy glm53-exl3-worker -n llm-test --replicas=1
kubectl wait --for=condition=Ready pod -l app=glm53-exl3-worker -n llm-test --timeout=1800s
```

## Step 4 — expose (optional, only once running)

```bash
kubectl apply --server-side -f llm-test/glm53-parity/services.yaml
```

Endpoint: `http://glm.taildeab2.ts.net/` (relay → `172.16.4.55:8000`). The vLLM
API itself listens on the head node's host network at `0.0.0.0:8000`.

## Verify

```bash
kubectl get pods,deploy,svc -n llm-test -o wide | grep glm53
kubectl logs -n llm-test deploy/glm53-exl3-head -c vllm --tail=100
kubectl logs -n llm-test deploy/glm53-exl3-worker -c vllm --tail=100
curl -i http://172.16.4.55:8000/health   # from a node / via tailnet
curl http://172.16.4.55:8000/v1/models
```

## Notes / caveats

- The overlay patches are **baked** into the public image at build time; the
  image's `glm53.recipe.stamp` ties it to the overlay/Dockerfile hash. The only
  two runtime-only patches (`patch_adaptive_k.py`, `patch_dense_fp8.py`) are
  delivered via `glm53-parity-overlay` and are **off by default**
  (`GLM53_ADAPTIVE_K=off`, `GLM53_DENSE_FP8=off`). The overlay loop guards each
  with `[ -f /opt/glm53/$p ]`.
- Boot-shape warmup (`scripts/boot-shape-warmup.sh`) runs post-`/health` in
  `start.sh` but is **nonfatal** and is not (yet) wired into this lane. It can be
  added as a post-ready Job/sidecar if uncovered JIT shapes are a concern.
- The API key is read by vLLM natively via `VLLM_API_KEY` (never argv). Set it in
  the Deployment env or a Secret before scaling; empty = unauthenticated.
- `EXTRA_ARGS` ships the default DFlash2 CUDA-graph capture list
  `--cudagraph-capture-sizes 1 2 4 8 16 24 32`. The adaptive-k / FP8-dense
  fast paths need a longer list and a KV cap; see the upstream `.env.example`.
- CX7 backplane: both nodes use **`enp1s0f1np1`** (RoCE device `mlx5_1`,
  GID index 2) carrying `172.16.5.55` (head) / `172.16.5.56` (worker). The
  generic `.env.example` defaults (`rocep1s0f1`/`rocep1s0f0`) do **not** match
  this kit, so the lane pins the correct per-node values.
