# model-cache-puller — generic Hugging Face cache puller/deleter

The one tool image for preloading (and evicting) model caches on the shared
`model-cache` volume in `llm-test`. What it does is declared entirely at Job
time via environment variables; the image itself is model-agnostic and stays
tiny (python + huggingface_hub + httpx + requests).

## Name history (read this before grepping for old refs)

The same code lineage has been pushed under three registry names:

| registry path | versions | status |
|---|---|---|
| `homelab/model-cache-downloader` | v1 | dead (original name, pre-glob code) |
| `homelab/glm53-cache-puller` | v1–v6, latest | **legacy alias — do not add new references.** The tool was never glm53-specific; the name stuck from its first use. Existing digest-pinned v6 Jobs keep working. |
| `homelab/model-cache-puller` | v7 | **canonical.** New Jobs use this. |

v7 (2026-11-18) is byte-identical `puller.py` to v6 —
`sha256 fbad2c4d88eedccec40708fdce28d40b355766c7080a5d60f3c103990c77cc5a` —
just rebranded. Migrating a Job is a one-line image swap with no behavior
change.

Canonical v7 reference:

```
registry.taildeab2.ts.net/homelab/model-cache-puller:v7@sha256:fedbacb21b9469e23aba9d847b78cfe6378337ce58ff9a8ffa3a96e7fd9f7708
```

(The digest is the manifest digest; `podman inspect .RepoDigests` after a pull
shows it.)

### Registry quirk: GET-by-digest returns MANIFEST_UNKNOWN

The garage S3-backed registry serves manifests by **tag** (`/manifests/v7`)
but rejects HTTP GET by digest (`/manifests/sha256:...`) with
`MANIFEST_UNKNOWN`, for every image — old and new. This is a registry-level
behavior, not a broken push: digest *pulls* via podman/containerd/kubelet
resolve fine. Consequences:

- Digest-pinning Jobs works; the kubelet pulls it successfully.
- Verifying a push with `curl .../manifests/sha256:...` gives a false 404.
  Verify with `podman pull ...@sha256:<digest>` instead.

## Build / push

Build native on an arm64 node (arm64 is the only runtime target; jobs run on
aarch64 nodes — chronometer, sextant, octant, astrolabe):

```bash
scp -r llm-test/puller chronometer:/tmp/puller-build && ssh chronometer 'cd /tmp/puller-build && podman build -t registry.taildeab2.ts.net/homelab/model-cache-puller:v8 . && podman push registry.taildeab2.ts.net/homelab/model-cache-puller:v8'
ssh chronometer 'podman pull -q registry.taildeab2.ts.net/homelab/model-cache-puller@sha256:<digest> && podman inspect --format "{{json .RepoDigests}}" <image>'   # get + verify the digest
```

Bump the version tag on any change to `puller.py` or the `Dockerfile`, pin the
new digest in Jobs, and append a changelog line to the `Dockerfile` header.

## Job parameters (env)

| var | required | default | meaning |
|---|---|---|---|
| `HF_HOME` | no | `/models/.cache/huggingface` | HF cache root (mount the `model-cache` PVC here) |
| `PULL_MODELS` | one of PULL/DELETE | — | comma-separated specs, grammar below |
| `DELETE_MODELS` | one of PULL/DELETE | — | comma-separated repo ids or bare cache dirs (`models--org--name`) |
| `RATE` | no | `104857600` | max aggregate bytes/sec across ALL files and repos (in-code token bucket). `0` = unlimited |
| `MAX_FILE_WORKERS` | no | `8` | concurrent file downloads, total |
| `MAX_REPO_WORKERS` | no | `2` | repos pulled in parallel |
| `MAX_DELETE_WORKERS` | no | `4` | concurrent deletes |
| `PROGRESS_INTERVAL` | no | `30` | seconds between progress logs; `0` disables |
| `RECEIPT_PATH` | no | — | if set, a JSON receipt of the pull is written there |
| `HF_TOKEN` | no | — | token for gated / rate-limited repos (usually from Secret `huggingface`) |
| `HF_ENDPOINT` | no | — | override the Hugging Face endpoint |
| `HF_HUB_DISABLE_XET` | recommended `1` | — | stream via plain HTTP (needed for the in-code rate cap to hold) |

### PULL_MODELS spec grammar

```
repo[@revision][#include-glob|include-glob|...]
```

- `revision` — a commit SHA or tag. **Pin a SHA**, not a tag, for anything
  durable: tags move.
- `#...` — optional include patterns (fnmatch globs matched against
  repo-relative paths, `|` between them). When present, only matching files
  download.

**Partial pulls are deliberate, with one safety rule:** when patterns are
present, `refs/main` is NOT written, so a partial tree can never be resolved
by plain repo id. Downstream pods must reference the snapshot by its commit
path (`.../snapshots/<sha>/...`), not by repo id. Full pulls (no `#`) do write
`refs/main`.

Interrupted downloads resume: partial files are kept as `<dest>.part` and
byte-range-resumed.

### Example: full snapshot

```yaml
env:
  - name: PULL_MODELS
    value: "zai-org/GLM-5.3-BF16@9e25c28a2e8808d8b2599d780521fd6af24e7558"
```

### Example: partial pull (one width tier out of a 782 GiB multi-width repo)

```yaml
env:
  - name: PULL_MODELS
    value: >-
      kindlingai/glm-5.3-exlr8-k2-k3-k4@9e25c28a2e8808d8b2599d780521fd6af24e7558#config.json|generation_config.json|tokenizer*.json|chat_template.jinja|manifests/*|dense/*|index-slices/tp4/*|experts/*.index.safetensors|experts/*.k4.safetensors
```

(later: `experts/exlr8-layer-0*.k3.safetensors` can be added as a second
spec of the same repo to extend the tree in place — the puller skips files
already present at the expected size, so re-running is incremental and cheap.)

### Example: delete

```yaml
env:
  - name: DELETE_MODELS
    value: "org/Abandoned-Model,models--org--old-experiment"
```

## Receipt / verification pattern

The image writes a basic receipt when `RECEIPT_PATH` is set. Stronger
lane-specific verification (shard-set checks, weight-index cross-checks,
hash-file verification) is done by the calling Job's args script after
`python3 /opt/puller/puller.py` — see
`conductor-workloads/workloads/flare-glm53/05-model-download.yaml` or
`workloads/glm53-flash-1104/01-download-model.yaml` for the established
pattern: pull → verify → write lane receipt → touch completion marker.

## Conventions for new cache-preload Jobs

1. `spec.suspend: true` — GitOps renders the Job but nothing runs until an
   operator un-suspends (keeps Argo from re-triggering completed pulls).
2. `backoffLimit: 2147483647`, `restartPolicy: OnFailure` — large pulls
   resume, not restart, on failure.
3. Pin the image by digest (v7 reference above).
4. Node-select the puller onto one node (chronometer historically) — the
   volume is RWX, so any node works; pinning keeps juicefs cache locality.
5. One lane per repo+revision: never let two lanes' verify scripts assert
   about the same snapshot path.

## Code

- `puller.py` — the tool (single file, ~470 lines, stdlib + huggingface_hub).
- `Dockerfile` — build recipe + changelog.
- `puller-job.yaml` — copy-paste Job template.
