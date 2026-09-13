# DeepSeek-V4.1-Flash EXL3 (2.9 bpw) — download prep, handoff for review

**Status: DOWNLOAD COMPLETE.** The cache-pull Job completed on 2026-09-13.
Puller v5 preserves interrupted `.part` files for HTTP byte-range resume; the
Job uses a versioned tag with `imagePullPolicy: Always` because this private
registry does not resolve Podman's reported digest through containerd. No
serving lane was changed.

**Serving lane: PREPARED in `llm-test/dsv41-parity/`** (README with the full
recipe→K8s mapping, `05-prepare-model-tree.yaml` — hardlinks HF-cache
snapshots into stable serving trees + builds the embed-only Engram index,
`12-dsv41-parity.yaml` — profile/launch/warmup ConfigMaps + head/worker
Deployments at `replicas: 0`, `services.yaml`). Next step after this review:
apply the prep Job, then review the lane manifests before scaling anything.

Reviewer: this doc + the two files listed in §3 are the whole change. The
recipe clone lives at `/tmp/ds41-recipe` (upstream:
<https://github.com/MiaAI-Lab/DeepSeek-v4.1-Flash-EXL3-2x-DGX-Sparks>).

---

## 1. What the recipe is (and the two-checkpoint question)

MiaAI-Lab recipe serving `deepseek-ai/DeepSeek-V4.1-Flash` as an **EXL3 2.9 bpw
/ mul1** checkpoint on a 2× NVIDIA GB10 (DGX Spark) kit, TP=2 over CX7,
vLLM OpenAI-compatible on :8888, DSpark speculation built into the checkpoint
(no separate drafter repo). Image:
`ghcr.io/miaai-lab/deepseek-v4.1-flash-exl3-2x-dgx-sparks:2.9bpw` (public,
linux/arm64) — only needed at *serve* time, not for the download.

**Yes — two downloads are required**, and the user's "weights + engrams?"
suspicion is exactly right:

| # | HF repo @ pin | What | Size | Pulled how |
|---|---|---|---:|---|
| 1 | `Mia-AiLab/DeepSeek-V4.1-Flash-EXL3-2.9bpw` @ `64ba41b6c916a587db06eae2e19b7845f7be6e6b` | EXL3 quantized weights: 39 shards + config/quantization_config/tokenizer/chat_template (verified public, non-gated; 49 files via HF API) | **196.2 GiB** | full repo |
| 2 | `deepseek-ai/DeepSeek-V4.1-Flash` @ `dba1be0a40aa45a94ad051997016db3960a90277` | **Engram tables only**: `model-00047-of-00048.safetensors` (101,535,150,936 B), `model-00048-of-00048.safetensors` (101,537,926,640 B), `model.safetensors.index.json` (7,470,294 B) | **189.1 GiB** | partial (2 of 48 shards + index) |

Why partial: the Engram n-gram tables were never quantized and live **only** in
native shards 47+48 of the original checkpoint (`layers.{1,14}.engram.embed.{weight,scale}`,
~95 GiB per shard). The recipe never reads the other 46 shards (~287 GiB would
be pure waste). vLLM consumes them via `--hf-overrides '{"engram_table_dir":…}'`
pointing at the snapshot directory — repo-id resolution is *not* used for this
tree (and our v4 puller deliberately does not write `refs/main` for partial
pulls, see §2).

Total new cache data: **~385.3 GiB**. At the 100 MB/s RATE cap ≈ **70 min**;
real-world will be longer.

## 2. Why the puller was extended (v4/v5) — decision record

The generic cache-puller (`llm-test/puller/puller.py`) queues **every** file of
a repo; it had no partial-pull capability. Options considered:

- **A. Puller v4 with include filters** ← chosen. ~20-line additive change;
  keeps the in-code `RATE` limiter (household bandwidth cap is a hard
  requirement on the 1G site link); partial-repo pulls are a recurring need in
  this lane (engram/drafter/tower shards). Spec syntax:
  `repo[@revision][#glob|glob]` (`#` cannot appear in repo ids or SHAs).
  Backward compatible: no `#` → identical v3 behavior. **Full pulls still write
  `refs/main`; partial pulls intentionally do not** — a partial tree (3 files)
  must never be resolvable by repo id, otherwise some tool doing
  `vllm serve deepseek-ai/DeepSeek-V4.1-Flash` would find a snapshot missing
  `config.json`. Serving must reference the snapshot **by path**.
- **B. No puller change; job overrides `command` with
  `snapshot_download(allow_patterns=…)` on the existing `:v3` image.** Works
  with zero rebuild, but loses RATE pacing (would saturate the link) and is a
  one-off. Recorded as the **fallback** if v4 build is unwanted.
- Rejected: pulling the full native repo (wastes ~287 GiB of a 1 Ti PVC).

Gates before apply:
1. [DONE 2026-09-13] v5 built on sextant (aarch64, podman 5.8.6) from the
   reviewed `puller.py` and pushed as `glm53-cache-puller:v5`. Podman reported
   digest `sha256:e3205a77d0264cd1520fcc41c66005131ea0c589abe77b9a345eb73f59b76a02`,
   but this private registry does not resolve that digest through containerd,
   so the Job uses the versioned tag with `imagePullPolicy: Always`. v5 adds
   tested HTTP byte-range resume and declares `httpx` directly.
2. [DONE 2026-09-13] Larger-model download review completed; the pinned EXL3
   repo and native Engram shards 47/48 plus index match the upstream recipe.
3. [DONE 2026-09-13] The 1 TiB PVC had 572 GiB free before the ~385.3 GiB pull,
   so expansion was not required.

## 3. Files changed / added

| File | Change |
|---|---|
| `llm-test/puller/puller.py` | v4 adds partial include filters; v5 preserves `.part` files and resumes them with validated HTTP Range responses. |
| `llm-test/puller/Dockerfile` | v5 build instructions and explicit `httpx` dependency. |
| `llm-test/40-dsv41-flash-exl3-download.yaml` | **New** Job `dsv41-exl3-cache-pull`: both pulls via `PULL_MODELS` (full EXL3 + partial engram), `RATE=100000000`, pinned revisions, post-pull verification (39-shard count, required files, exact byte sizes for the 3 engram files), completion marker `/models/.dsv41-exl3-download-complete`, `nodeSelector: chronometer`, `backoffLimit: max` (resumable). Header states the NOT-APPLIED status and gates. |

Not changed: `apps.yaml`, `clusters/*`, any running Deployment/Job, any image in
the registry, the serving lanes.

## 4. Disk math (reviewer: verify before apply)

PVC `model-cache` (llm-test, JuiceFS RWX) requests **1 Ti**. Known/planned
occupants: DeepSeek vision-exp snapshot (large, tens of GiB+), GLM EXL3
~164 GiB, Qwen planned ~126 GiB, stale `LibertAIDAI/GLM-5.3-Flash-NVFP4`
(deletion pending via glm53 job). Adding **~385.3 GiB** may not fit.

Pre-flight (needs exec perms on the JuiceFS mount pod, e.g.:

```bash
kubectl get pods -n llm-test   # find juicefs *-mount pod for pvc-afa2ecdd-…
kubectl exec -n llm-test <juicefs-mount-pod> -- df -h /jfs   # usage of the volume
```

or `juicefs status`/`juicefs info` with the same metadata URL).

**Update: resolved by user** — the PVC can be expanded and space is not a
concern. Proceed without the headroom pre-flight (expand the JuiceFS
quota first if it ever reports pressure). If tight,
options: raise the PVC request (JuiceFS quota), delete the stale NVFP4 cache
first, or skip caching shard 47/48 separately if a full
`DeepSeek-V4.1-Flash` tree already exists somewhere reachable (point
`engram_table_dir` at it — the recipe explicitly supports reusing an existing
native tree: "Point `ENGRAM_DIR` at an existing DeepSeek-V4.1-Flash tree to
skip that half").

## 5. Serving-side notes (explicitly OUT of scope here)

When (if) this model should be *served* on the K8s lane, a reviewer should know
the recipe assumes a **2-node docker pair** (head `10.0.0.1` + worker, NFS or
ZFS weight sync), not our chronometer+sextant TP=2 topology. Differences to
resolve at that time: container/volume mapping (`dsv41-exl3-weights` → `/model`,
`dsv41-exl3-engram` → `/engram-src`), `prepare_engram_src.py` hardlink step,
DSpark config (`{"method":"dspark","num_speculative_tokens":3}`), parsers
(`deepseek_v41`), KV (`fp8_ds_mla`, do NOT set `--kv-cache-dtype`),
`MAX_MODEL_LEN=600000` / 2.5 GiB KV pool memory discipline, and the fact that
the recipe image ships its own vLLM (`0.1.dev20904+g179dd0fa9`) + EXL3 overlay.

**Ports/slots: resolved by user.** Lanes are slots — only one model is
loaded/scaled at a time, never two residents. The new lane can take port 8000
(or any free slot) at serve time; there is no 8888 collision to design around.

## 6. Open questions for the larger model

1. ~~Disk capacity~~ — **answered**: PVC expandable, proceed (§4).
2. Bandwidth window: RATE 100 MB/s okay, or lower for daytime? Job is
   resumable, so it can also be split across nights.
3. Engram reuse: is there already a full `deepseek-ai/DeepSeek-V4.1-Flash`
   tree in some cache we should reuse instead of the 189 GiB partial pull?
   Default if unknown: proceed with the partial pull as prepared.
4. ~~Image trust~~ — **answered**: v4 built and pushed from the reviewed diff;
   digest in §2 gate 1.
5. Serving manifest timing: create the serving lane (mirroring
   `glm53-parity/`) now, or after the download completes? Slot model applies:
   one resident model at a time, port 8000 available.
