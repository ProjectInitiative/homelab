# Model-Swap Router + Controller — Plan (for review)

Status: DRAFT. Not applied. Cluster access is read-only (MCP); this is a design
document. Apply steps are manual unless explicitly marked GitOps.

---

## 0. Constraint recap (why this is shaped the way it is)

- **Two DGX Sparks (GB10).** Every model is a 2-node `TP=2`/`nnodes=2` vLLM
  deployment that consumes **both** nodes via `hostNetwork` on fixed fabric IPs
  (`172.16.4.55` head / `172.16.4.56` worker) and per-model master ports.
- **Only one model is resident at a time.** This is a **model-on-demand / slot**
  problem, not a load-balancer-across-N-models problem.
- **Startup time is a *staging* vs *swap* split, not a single number.** Once the
  weights are cached and the JIT caches are warm, a swap is dominated by loading
  weights into GB10 **unified memory** + engine init — not by download/compile.
  See §0.1.
- **Each model has a bespoke deployment cycle**, not an image swap. Each has its
  own image, huge per-model env profile, init-container patch staging, hostPath
  JIT caches, and served-model-name:

  | Model | Image | Served name | Head port | Notes |
  |---|---|---|---|---|
  | DeepSeek | `ghcr.io/anemll/dspark-vllm-gx10:…@sha256:a83948…` | `deepseek-v4-flash-vision-exp` | 8000 | Anemll DSpark + many hotfixes |
  | GLM | `ghcr.io/miaai-lab/glm-5.3-flash-2x-dgx-sparks:exl3` | `GLM-5.3-Flash-EXL3` | 8888 | EXL3, DFlash2, own overlay |
  | Qwen | `vllm/vllm-openai:qwen38-flash-next` | `qwen3.8-flash-next` | 8888 | NVFP4, PLE/MXFP8 patches, MTP3 |

### 0.1 Startup-time model: staging (one-time) vs swap (recurring)

Your read is correct — once the weights are downloaded and cached, the spin-up
is ~the unified-memory weight load. Split the lifecycle:

**Stage-once (per model, do ahead of time)** — expensive, rate-limited by
network/storage download + first-ever kernel compile:

1. Download weights to the shared cache (existing `*-download` Jobs; JuiceFS
   `model-cache` / per-model HM cache). For Qwen this is ~126 GiB, GLM ~164 GiB.
2. Run **one full boot** to populate the per-node **JIT caches** (Triton /
   TileLang / B12X / FlashInfer / vLLM) and run the **boot-shape warmup** sweep.
   These are mounted on `hostPath` (`/var/lib/llm-test/jit-cache/*`) precisely
   so a warm boot skips re-JIT. This is why the DeepSeek profile stresses
   persisting `TRITON_CACHE_DIR` / `TILELANG_CACHE_DIR` / `B12X_CUTE_CACHE_DIR`.

**Swap (recurring, the actual "spin-up")** — bounded by loading into memory:

| Model | Measured boot | Dominant cost once cached |
|---|---|---|
| Qwen | ~10m55s (cold, already-downloaded) | weight load **~458 s** (392 s target + 67 s MTP) + engine init ~92 s + graph capture ~7 s |
| GLM  | launcher `READY_TIMEOUT` 3600 s default | weight load (~164 GiB) + engine init + JIT if cold |
| DeepSeek | — | weight load into UMA + engine init; JIT warm from hostPath caches |

So after staging, a swap is roughly **weight-load + engine-init, i.e. on the
order of ~10–15 min** for the big checkpoints (bandwidth-bound reading
126–164 GiB into unified memory), and **much faster** if the JIT caches are warm
(first request doesn't pay the FlashInfer/Triton autotune). The launchers already
poll `/health` with long timeouts to gate on this.

Implication: keep weights + JIT caches **stage-once**, and the recurring swap is
just the scale-down/up + load + `/health` gate that the controller drives. This
is why the controller code stays simple — it never downloads or compiles.

---

## 1. Architecture — two layers

```
Tailscale `ai` Service ──► LiteLLM router (auth, virtual model names, /v1/models)
                                  │  api_base → per-model hostNetwork endpoint
                                  │
                    Fission swap controller (event-driven, no container to maintain)
                        HTTP trigger  ── "load <model>" / "status"
                        Timer trigger ── scheduled swap
                        KuberWatch    ── react to deployment ready / pod health
                        function does:
                          scale down old head+worker → wait gone
                          scale up target worker → head
                          wait /health (long)
                          update model-state + LiteLLM config (hide old, show new)
```

**Layer A — the router/data plane = LiteLLM.** Replaces the hand-pinned
`ai-proxy` HAProxy relay. OpenAI-compatible, virtual model names, per-user/team
keys + budgets ("permissions"), `model_group_alias` with `hidden: true` so an
evicted model drops off `/v1/models`, `order`-based fallback. Runs as a normal
Deployment behind a Service; the Tailscale `ai` LoadBalancer points at it.

**Layer B — the swap controller = Fission functions.** This is the custom part.
Nothing off-the-shelf does the scale-down/up + long-readiness + mutual-exclusion
dance. See §3.

---

## 2. Layer A — LiteLLM router (replaces HAProxy)

Files (new, under `llm-test/router/`):

- `litellm-config.yaml` — ConfigMap. Three virtual model entries, one per model:

  ```yaml
  model_list:
    - model_name: deepseek-v4-flash-vision-exp
      litellm_params:
        model: hosted_vllm/deepseek-v4-flash-vision-exp
        api_base: http://172.16.4.55:8000/v1
        api_key: os.environ/VLLM_API_KEY
    - model_name: GLM-5.3-Flash-EXL3
      litellm_params:
        model: hosted_vllm/GLM-5.3-Flash-EXL3
        api_base: http://172.16.4.55:8888/v1
        api_key: os.environ/VLLM_API_KEY
    - model_name: qwen3.8-flash-next
      litellm_params:
        model: hosted_vllm/qwen3.8-flash-next
        api_base: http://172.16.4.55:8888/v1
        api_key: os.environ/VLLM_API_KEY
  router_settings: { model_group_alias: {} }   # aliases managed by controller; hidden:true for evicted
  ```

  > Note: GLM and Qwen share the same head port (8888) but are never resident
  > simultaneously, so there is no conflict. Each entry points at the same
  > `172.16.4.55` host IP — same reachability path the HAProxy relay uses today.

- `litellm-deployment.yaml` — Deployment + Service `llm-router` (port 8000). Set
  `functionTimeout`/request path not needed here; just a normal web pod.
- `litellm-values` / operator notes: LiteLLM reads config from a mounted
  ConfigMap and supports hot reload on config update (`on_settings_update`), so
  the controller can toggle which model is live **without restarting the router**.
- Updated `ai` Service → selector `app: llm-router`; **delete `ai-proxy`**
  (HAProxy) Deployment/Service/ConfigMap.

Auth/permissions: create virtual keys per team/user via LiteLLM; optionally a
single `VLLM_API_KEY` matched to each backend (note DeepSeek uses
`DSPARK_API_KEYS`/`VLLM_API_KEY`, GLM/Qwen use `VLLM_API_KEY`).

---

## 3. Layer B — Fission-based swap controller

### 3.1 Why Fission (your question)

Fission is well-suited **specifically** to the "custom code, no container/dev
cycle" goal:

- **You write plain code, not a container.** A function is code + a reference to
  a runtime Environment + a Package. No Dockerfile/Deployment/Service to
  maintain; Fission derives the pod and scales it.
- **The trigger model maps directly to the swap lifecycle**:
  - **HTTP trigger** — `POST /load` (model name in body/path) to request a swap,
    `GET /status` to inspect current/available models.
  - **Timer trigger** (cron) — e.g. daily/weekly scheduled swap.
  - **Kubernetes watch trigger** — fire on the target Deployment becoming ready,
    which is the natural "advance the state machine" event and avoids holding an
    HTTP request open for 30+ min (see §3.4).
- **Code changes = new package, no image rebuild.** Source-package build means
  editing a `.py`, rebuilding the package, done. That's the dev-cycle saving.

The long cold start is the one thing to design around (below). The swap logic
itself is small: pick model, scale deployments, poll `/health`, update state.

### 3.2 Fission objects

- **Environment** — `python` (or `python3.12`). Installed libs: `kubernetes`
  or `pykube`/`requests` for the k8s API, `pyyaml`. Pin deps in the environment
  spec so functions just `import fns`.
- **Functions** (`fission.io/v1`):
  - `swap-load` (HTTP) — validate request, acquire single-flight lock, record
    desired model, return immediately (async).
  - `swap-finalize` (Kubernetes watch on `apps/v1 Deployment` in `llm-test`)
    — when the target `*-head` reaches Ready, mark model ready, update model-state
    ConfigMap, update LiteLLM `router_settings` (hide evicted / show resident),
    release the lock.
  - `swap-progress` (HTTP) — poll state (for a client that wants sync-ish UX).
  - `model-status` (HTTP) — list available + resident + evicted.
  - `swap-schedule` (Timer) — optional scheduled swap (e.g. `0 2 * * *`).

### 3.3 Swap sequence (the documented "deployment cycle")

1. Acquire a **single-flight lock** (only one swap at a time / one resident
   model). Use a ConfigMap or Redis lease. If a swap is in progress, reject or
   queue.
2. **Drain/scale down** current `-head` + `-worker`; wait for both to be gone
   (honor `terminationGracePeriodSeconds`, Ray/NCCL teardown).
3. **Scale up** target `-worker` **first**, then `-head` (matches the documented
   worker→head order in the parity README and both upstream `start.sh`s).
4. **Wait for readiness** — poll the head's host IP `/health` until 200 (long
   timeout). Optionally trigger the boot-shape warmup sweep the launchers run.
5. **Publish state** — mark model `ready`, update `model-state` ConfigMap, tell
   LiteLLM which model is live (and mark the others `hidden:true` so they leave
   `/v1/models`).
6. Release lock.

### 3.4 ⚠️ Long-running caveat (the main gotcha)

Fission `functionTimeout` **defaults to 60 s**. Even a warm swap (weight load +
engine init) is several minutes — far over the 60 s default. Two ways around it;
**recommend the event-driven path**:

- **Event-driven (recommended):** `swap-load` only *kicks off* the swap and
  returns a job/state id in milliseconds. The actual "wait for readiness" is
  driven by a **Kubernetes watch trigger** on the Deployment, so no HTTP request
  is held open. Each step is a short function invocation.
- **Long streaming (alternative):** set the function to `streaming: true` with a
  large `maxDurationSeconds` / `idleTimeoutSeconds` and have `swap-load` stream
  progress. Simpler client UX, but holds a connection open across the whole load
  and fights proxies. Only if you don't want the watch-trigger plumbing.

### 3.5 Cluster access from functions

- Function pods run **in-cluster**, so they can use the in-cluster kubeconfig,
  exactly like the existing MCP agent. No kubeconfig file needed.
- Give Fission the RBAC to: `scale` Deployments in `llm-test`, `get/list/watch`
  Deployments & Pods, `get/create/update` ConfigMaps (state + LiteLLM config),
  `get/list/watch` the model `-head`/`-worker` pods.
- Fission function pods need a **ServiceAccount** with that RBAC. Fission lets you
  set a `ServiceAccountName` (and pod-spec overrides like `nodeSelector`,
  `resources`) on the function/environment so the function can run pinned to
  `chronometer` if it needs to reach the host-network endpoint directly.
- Confirm the function pod can route to `172.16.4.55:<port>` (same path the
  HAProxy relay uses today — should be fine).

### 3.6 State & config

- **`model-state` ConfigMap** (source of truth): `resident`, `desired`,
  `status`, `started_at`. Functions read/write it; `model-status` reads it.
- **`model-profiles` ConfigMap** (per-model constants, so controller code stays
  model-agnostic): deployment names (head/worker), head host IP + port, served
  model name, `/health` path, expected ready timeout.
- **LiteLLM config** — updated by `swap-finalize` via `on_settings_update`
  (mark evicted models `hidden`, resident live).

---

## 4. RBAC (target)

| Resource | Verbs | Why |
|---|---|---|
| `deployments.apps` (llm-test) | get, list, watch, patch, update | scale head/worker up/down |
| `pods` (llm-test) | get, list, watch | wait-for-delete / ready |
| `configmaps` (llm-test) | get, create, update, patch | state + LiteLLM config |
| `services` (llm-test) | get, list | resolve head endpoint |
| `leases` or `configmaps` | get, create, update | single-flight lock |

Applied to a ServiceAccount used by the Fission function environment.

---

## 5. Prereqs / rollout order

1. **Install Fission** (helm) + Python environment + the ServiceAccount/RBAC above.
2. **Deploy LiteLLM router**; point Tailscale `ai` at it; confirm `/v1/models`
   shows the resident DeepSeek model; **remove `ai-proxy`**.
3. **Shape per-model Deployments** as generic head/worker templates defaulting to
   `replicas: 0` (GLM, Qwen analogous to `12-deepseek-miaai-parity.yaml`), plus a
   GLM/Qwen model cache preload Job.
5. **Stage all three models once** (weights already on the shared cache from
   the existing `*-download` Jobs) and run a **boot-shape warmup** boot per model
   so Triton/TileLang/B12X/FlashInfer JIT caches are warm on `hostPath`. After
   this, swaps are load-into-RAM, not download.
6. **Deploy Fission functions** (`swap-load`, `swap-finalize`, `model-status`).
7. **Test the swap** deepseek → glm → qwen → back, and verify:
   - mutual exclusion (only one head+worker up),
   - readiness gate actually waits for `/health`,
   - `/v1/models` reflects the resident model and evicted models are hidden,
   - auth keys still work through LiteLLM.

---

## 6. Scheduling policy (FIFO + priority + traffic light)

Your model is a **single residency slot with a high setup cost** — the classic
"avoid thrashing a cache" scheduling problem. Frame it as: per-model **FIFO
queues**, and across models a **priority + per-model quantum (round-robin)**
"traffic light." No proactive eviction; a model is only unloaded when a
*different* model is actually wanted.

### 6.1 Model

- **One residency slot** (`resident`). Idle eviction is never done proactively;
  eviction is purely demand-driven.
- **Per-model FIFO queue** `Q_m` — requests for a non-resident model queue here
  (ordering by arrival within a model).
- **Traffic light / quantum** — a model serves up to `max_requests_m` **OR**
  `max_seconds_m` per turn, then the light goes red. Newly arriving requests for
  that model park in a **fresh bucket** for its next turn (this is the "cut off").
- **Cross-model scheduler** — within a round, serve models with non-empty queues
  in **priority order**; each drains up to its quantum. Round-robin so a busy
  high-priority model can't starve lower ones; priority is expressed as **quantum
  size / turns per round (weighted)**.

Example: `deepseek #1` (quantum = 32 reqs or 10 min), `qwen #2`, `glm #3`. Drain
deepseek's window, red-light (its new requests go to the next bucket), serve
qwen's window, then glm, then back to deepseek. Deepseek gets the bulk, but
qwen/glm **always** get a turn → no starvation, bounded switch frequency.

### 6.2 Anti-thrash rules

- **Stickiness:** don't evict `resident` unless another model's queue is
  non-empty **and** resident's queue is empty or its quantum expired.
- **No preemption:** never interrupt a draining resident.
- **Min dwell** (`min_dwell_m`): stay resident at least this long once loaded, to
  amortize the ~10–15 min load.
- **Cooldown** (`cooldown_m`): minimum time before switching back to a model that
  just had a turn.

### 6.3 Knobs

| Knob | Meaning |
|---|---|
| `priority_m` | ordering / weight per model |
| `max_requests_m` / `max_seconds_m` | per-turn drain cap (the "traffic light") |
| `min_dwell_m` | min residency to amortize the load |
| `cooldown_m` | min time before switching back |
| `window_seconds` | scheduler tick |

### 6.4 Where requests are parked (the crux)

Requests arrive at a synchronous OpenAI API. When the target model is not in a
green window, the router must hold them. Two options:

- **Stream-hold (OpenAI-compatible, recommended):** the router accepts the
  request, holds the connection open (long idle/stream), and replays it when the
  model gets its green window. Send periodic keepalive/Comment bytes so clients
  and proxies don't time out. Cost: clients see a long TTFT (load + queue
  position).
- **Async job queue:** return a ticket/id immediately; client polls or subscribes
  and retrieves the result later. Robust to 15-min loads but **changes the API
  contract** (not standard `/v1/chat/completions`).

Recommend stream-hold for standard OpenAI clients (with generous timeouts), and
optionally expose a job endpoint for long-running callers.

> **Honest note on Fission vs a service:** the scheduling state machine above
> (queues, priorities, min-dwell/cooldown timers, single-flight, cut-off
> admission) is **stateful and long-running** — that's better as a small
> persisting **scheduler service** than Fission's ephemeral HTTP functions.
> Fission is the right tool for the discrete, stateless **surface ops** (swap
> request endpoint, model-ready KubernetesWatch, status endpoints). So Layer B
> becomes: a small **scheduler service** (the "custom code" → its own entity) +
> **Fission** for the perimeter event handlers.

---

## 7. Open questions / risks

- **Single-flight lock** needs to be robust (crash during swap shouldn't
  deadlock). Consider a lease with TTL + watch-trigger recovery.
- **HostNetwork port conflicts** — because IPs/ports are shared, the controller
  must *guarantee* the old pair is fully gone before scaling the new one up.
  Racing here causes NCCL/port binds to fail.
- **Reachability** of host-network endpoint from the function pod (same as the
  relay today; confirm before committing to the design).
- **Cold-start length** — even if the recurring swap is ~10–15 min of
  weight-load + engine-init (not a download), that's still a window of GPU
  idleness during a swap. Decide whether to accept it, or pre-load a standby
  model and swap only when the standby is ready.
- **LiteLLM hot-reload** — verify `on_settings_update` behavior for adding/hiding
  model groups meets the "no router restart" goal; fall back to a rolling restart
  of the LiteLLM Deployment if not.
- **GitOps** — `llm-test` is intentionally outside GitOps today. Decide whether
  the router + Fission functions join Argo CD later (recommended once stable).
- **Licensing** — the GLM/Qwen deploy repos are AGPL-3.0; the *controller code we
  write* is ours (Fission functions we author), so no AGPL obligation unless we
  copy their files. Keep our functions original.

---

## 8. Repository & GitOps boundary (proposal)

Move the serving platform into its **own repo**, generated with CDK8s, consumed
by Argo CD via the cdk8s CMP plugin (the same pattern as this homelab repo).
Keep the homelab repo **lean** — it only registers the new repo as an Argo CD
Application (one Application CR / root parent entry); the new repo self-contains
the whole serving stack + its custom code.

### 8.1 Assumed cluster-provided (NOT owned by the new repo)

| Resource | Assumed present |
|---|---|
| Argo CD + a project, and the cdk8s CMP plugin | yes |
| Shared StorageClass `juicefs-sc` + the HuggingFace `model-cache` volume | yes |
| Fission installed + a Python environment (and in-cluster k8s action) | yes |
| NVIDIA device plugin advertising `nvidia.com/gpu` on chronometer/sextant | yes |
| Tailscale LoadBalancer + `mc-ingress-proxy` proxy-group for the `ai` Service | yes |
| OpenBao/VSO for the HF token (or pre-staged public weights) | yes |
| Node `hostPath` `/var/lib/llm-test/jit-cache/*` for JIT caches | yes (per-node) |

### 8.2 New repo layout

```
└── <serving repo>
    ├── generator/            # CDK8s app: main.py + cdk8s.yaml + imports
    │                         #   → renders Argo CD Application CRDs / component manifests
    ├── deploy.yaml           # catalog-style inputs (mirrors apps.yaml / clusters.yaml)
    ├── apps/                 # per-model head/worker templates (replicas: 0)
    │   ├── deepseek/  glm/  qwen/   # image, port, served name, /health
    │   └── model-profiles.yaml
    ├── router/               # LiteLLM (Helm source + ConfigMap) + Tailscale `ai` Service
    ├── scheduler/            # CUSTOM CODE: source + Dockerfile + CI build/push
    ├── fission/              # function sources + Environment/Package/Function/Trigger
    ├── k8s/rbac.yaml         # namespaced ServiceAccount/Role/RoleBinding for scheduler + fns
    └── cache/                # weight preload + boot-shape warmup Jobs
```

### 8.3 Custom code as its own entity

The **scheduler** is the one piece of real custom code. Build it in this repo
(GitHub Actions → image registry), reference it by **image tag** in the
CDK8s-generated Deployment. GitOps stays lean: bumping the version is a CI/image
change, not a manifest edit. The Fission function sources/packages ship as
declarative resources in the same repo.

### 8.4 Wiring into the cluster

- New namespace (reuse `llm-test` for now, or a prod `llm-serving`).
- Add one Argo CD `Application` (destination `mc`, project e.g. `llm-serving`)
  with `spec.source.repoURL = <serving repo>`, the cdk8s `plugin`, and a `path`,
  via the existing `parent-apps` / root pattern in the lean repo.

### 8.5 Open questions

- Repo name/location and whether it starts with `generator/` mirroring homelab or
  a slimmer single-file generated output.
- **Scheduler as container image vs Fission `newdeploy` function** — recommend
  image (it's stateful; and it's literally the "custom code entity").
- Whether the new repo owns **namespaced** RBAC (recommend yes, scoped to its
  namespace) or assumes a cluster-level ServiceAccount.
- Model weights source — public vs gated HF (Qwen `ABLIT=1` needs the token) and
  where the token comes from (OpenBao/VSO).
- Model-cache volume: per-model subpath on the shared JuiceFS, and where the
  one-time warmup boot lives (a Fission/Job in this repo, run once per model).
