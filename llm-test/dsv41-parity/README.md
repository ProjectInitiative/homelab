# DeepSeek-V4.1-Flash EXL3 2.9bpw — K8s parity lane (2× GB10, TP=2)

Adaptation of the MiaAI-Lab docker recipe
(https://github.com/MiaAI-Lab/DeepSeek-v4.1-Flash-EXL3-2x-DGX-Sparks, local
clone `/tmp/ds41-recipe`) onto the homelab `llm-test` 2-node lane topology,
cloned from the proven `glm53-parity/` lane skeleton.

**Status: VALIDATED ON THE 2× GB10 LANE.** Resources still ship with
`replicas: 0`; activation remains an explicit worker-first slot swap.

## Files / apply order

| Order | File | What |
|---|---|---|
| 0 | `../40-dsv41-flash-exl3-download.yaml` | cache-pull Job (v5) — must have completed (`/models/.dsv41-exl3-download-complete`) |
| 1 | `05-prepare-model-tree.yaml` | Job `dsv41-model-tree-prep`: hardlinks the HF-cache snapshots into stable serving paths on the JuiceFS PVC (`/models/dsv41-exl3/model`, `/models/dsv41-exl3/engram-src`), builds the embed-only Engram index (recipe `scripts/prepare_engram_src.py` semantics), verifies byte sizes. Idempotent. |
| 2 | `06-warm-juicefs-cache.yaml` | Node-pinned Jobs that use native `juicefs warmup` to read every byte of the prepared EXL3 and Engram trees into each node's independent Gen4 NVMe block cache. Apply sextant first, then chronometer. |
| 3 | `07-pack-engram-local.yaml` | Retained node-affine `local-path-nvme-sticky` PV/PVC pairs plus idempotent Jobs that build each rank's ~94 GiB contiguous Engram row store on raw local NVMe. |
| 4 | `12-dsv41-parity.yaml` | profile/launch/warmup ConfigMaps + `dsv41-exl3-head` (chronometer) / `dsv41-exl3-worker` (sextant) Deployments, `replicas: 0` |
| 5 | `services.yaml` | ClusterIP Services `dsv41-head` / `dsv41-worker` (:8000). No ai-proxy/Tailscale LB yet — router wiring comes with the LiteLLM cutover (`router/PLAN.md`) |

## Serving contract (extracted from the recipe)

- Image `ghcr.io/miaai-lab/deepseek-v4.1-flash-exl3-2x-dgx-sparks:2.9bpw`
  (public, arm64, vLLM `0.1.dev20904+g179dd0fa9` + EXL3 overlay + SM121
  patches baked at `/opt/dsv41/`). The recipe bind-mounts repo overlay files
  over the baked ones to guarantee freshness; here we trust the image stamp —
  if the recipe's overlay ever drifts, mount the updated files via ConfigMap
  (the launch scripts' patch loop skips missing files by design).
- Two ranks, `--distributed-executor-backend mp`, `--nnodes 2 --node-rank 0/1`,
  head serves the API, worker `--headless`. Rank discovery via
  `--master-addr 172.16.5.55 --master-port 29721` (CX7 fabric IPs; NCCL rides
  `172.16.5.x`, API/LAN is `172.16.4.x` — do not mix planes).
- Served name `DeepSeek-v4.1-Flash-EXL3`, port **8000** (slot model: only one
  lane resident at a time; the GLM lane also sits on 8000 when resident).
- Speculation: in-checkpoint **DSpark** k=3 (`--speculative-config
  {"method":"dspark","num_speculative_tokens":3}`). `SPEC_METHOD=none` for
  wide-batch serving (measured faster at ×4 streams).
- KV: vLLM picks `fp8_ds_mla` itself — **never set `KV_CACHE_DTYPE`**.
  Pinned pool `KV_CACHE_MEMORY_BYTES=2684354560` (2.5 GiB, 774k tokens at
  600k ctx), `KV_BLOCK_SIZE=64` (SM12x indexer requirement).
- Text-only on GB10: `LANGUAGE_MODEL_ONLY=1` (FlashInfer SM120 sparse-MLA has
  no 1152-wide kernel yet).
- `/engram-src` remains the canonical file-backed source via
  `--hf-overrides {"engram_table_dir":"/engram-src"}` and contains shards
  47+48, the embed-only index, and `config.json`. At runtime
  `DSV41_PACKED_DIR=/engram-packed` attaches the rank-specific contiguous row
  stores from node-affine local NVMe PVCs, bypassing JuiceFS/FUSE for misses.
- Memory discipline knobs shipped as in the recipe: `MAX_NUM_SEQS=2`,
  `MAX_NUM_BATCHED_TOKENS=1024`, `DSV41_EXL3_SERIAL_STREAMS=1`,
  `VLLM_DISABLE_SHARED_EXPERTS_STREAM=1` (exllamav3 one-lock-buffer-per-device
  deadlock), `DSV41_PREFILL_EMPTY_CACHE_*`, `DSV41_IO_THREADS=32`,
  `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`. Memguard stays OFF
  (`DSV41_MEM_GUARD=0`) per the recipe's sustained-use finding.
- The launch scripts reproduce the recipe's inner-container behavior:
  GLM53_* vLLM-file exports, runtime EXL3 overlay install, the 11-patch loop
  (`patch_*.py`, all `[ -f ]`-guarded), fail-closed `/model` + `/engram-src`
  checks, then `exec vllm serve`.

## Deploy / swap procedure

1. Download Job complete → apply `05-prepare-model-tree.yaml` → wait for
   `/models/.dsv41-exl3/.prep-complete` (job success).
2. Apply `06-warm-juicefs-cache.yaml` for **sextant first**, wait for completion,
   then chronometer. The native JuiceFS warmer populates the configured 550 GB
   node-local NVMe caches and evicts older FIFO blocks without duplicating files.
3. Apply `07-pack-engram-local.yaml`; wait for both pack Jobs. Each retained
   local PVC must contain `engram-l{1,14}-r<rank>of2.bin` (~94 GiB total).
4. Scale **worker first, then head** (`kubectl scale deploy/dsv41-exl3-worker
   --replicas=1` then the head). Rank 1 joins the rank-0 master.
5. Head readiness = pod-local `/run/dsv41/dsv41-warmup-ready`: the background
   subshell polls `/health`, runs the thinking-off smoke and shape sweep, then
   marks the pod ready.
6. Slot swap: scale the old lane down first; port 8000 is only free when no
   other lane is resident (router/PLAN.md slot model).

## Deliberate deltas vs the recipe (reviewer attention)

1. **Topology/cache**: recipe = 2 docker hosts + NFS/ZFS weight sync; lane =
   2 pods + shared RWX JuiceFS. Chronometer and sextant each have an independent
   550 GB JuiceFS cache on local Gen4 NVMe. A cold Engram path measured only
   0.1–0.3 tok/s, so the node-pinned native cache warmers are a required
   pre-deploy step; warm reads remain JuiceFS-addressed but hit local NVMe.
2. **JIT caches** are node-local hostPaths
   (`/var/lib/llm-test/jit-cache/{vllm-cache,triton,tilelang,dsv41-tmp}`),
   mirroring GLM lane. First boot per node pays full JIT (~tune + kernels).
3. **`CHAT_TEMPLATE` is unset** — the EXL3 checkpoint ships its own
   `chat_template.jinja`; the recipe mounts its repo copy. If reasoning
   formatting differs, mount `files/chat_template.jinja` via ConfigMap and set
   `CHAT_TEMPLATE` (scripts already support it).
4. **Packed Engram is required here**: fully warmed JuiceFS delivered ~1 GiB/s
   sequentially but only 380–434 random 4 KiB IOPS (2.3–2.6 ms), versus
   12.8–13.4k IOPS (~0.076 ms) on raw NVMe. The un-packed lane plateaued near
   4.2 tok/s, so `07-pack-engram-local.yaml` implements upstream's local pack.
5. **`--oom-score-adj 1000`** is not expressible in a pod spec (no ulimit /
   oom-score API); GB10 driver allocations outside RSS remain a kernel-OOM
   blind spot, as the recipe documents. Memguard intentionally off.
6. **No NFS/ZFS/rsync code paths** — WEIGHT_SYNC is structurally "shared FS".
7. `MASTER_PORT=29721` is dsv41-lane-unique (GLM 29521, DeepSeek 25000).

## Validated K8s performance

With Engram addressed through fully warmed JuiceFS, random 4 KiB reads measured
only 380–434 IOPS (2.3–2.6 ms) despite ~1 GiB/s sequential throughput, and
structured decode plateaued near 4.2 tok/s. Raw node-local NVMe measured
12.8–13.4k IOPS (~0.076 ms). After attaching the per-rank packed local stores:

- count 1→200: 400 completion tokens, 0.410 s TTFT, **42.39 tok/s** decode
  (upstream reference ~40 tok/s);
- 400-token technical prose: 0.724 s TTFT, **28.53 tok/s** decode
  (upstream reference 31.6 tok/s);
- both ranks Ready with zero restarts; boot-shape warmup passed.

JuiceFS `writeback` is intentionally not enabled: it affects write durability,
not this read-only latency path. `cache-partial-only` is also unsuitable for the
fully prewarmed model because it optimizes cache capacity when sequential object
storage throughput exceeds local cache throughput, but does not bypass FUSE.

## Open items for review

- Verify `chat_template.jinja` in the EXL3 checkpoint renders reasoning
  identically to the recipe's ported template (delta #3).
- Confirm the fabric IPs from the GLM lane (`172.16.5.55/.56`) and CX7 pins
  (`enp1s0f1np1`, `mlx5_1:1`, GID 2) hold for this kit — copied from
  `glm53-parity` (K8s-proven) rather than the recipe's docker values
  (GID 3 / different ifnames) on purpose.
- Decide ai-proxy/LiteLLM exposure after first healthy boot.
