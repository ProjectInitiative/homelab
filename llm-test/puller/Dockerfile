# model-cache-puller — generic Hugging Face cache puller / deleter image.
#
# THE canonical model-cache preload image for llm-test. Model-agnostic: what to
# pull is declared entirely at Job time via env (see puller.py docstring).
#
# NAME POLICY: this image was historically built/pushed as
# homelab/glm53-cache-puller:v1-v6 (a misnomer — the tool was never glm53-
# specific) and even earlier as homelab/model-cache-downloader:v1. All three
# names are the same code lineage. New Jobs MUST reference
# homelab/model-cache-puller:<version>@sha256:<digest>; do not add new
# references to the old names. Existing glm53-cache-puller:v6 Jobs can migrate
# opportunistically to v7 (functionally identical code).
#
# Minimal. Only needs Python + huggingface_hub + httpx + requests.
# Pulls are rate-limited *in code* (token bucket on the HTTP session), so no
# tc/iproute2 is required in the image - throttling is fully controllable via
# the RATE parameter at job time.
#
# NOTE (registry quirk, do not "fix"): this registry (garage S3-backed)
# serves manifests by TAG (name:tag) but rejects GET-by-digest
# (name@sha256:...) with MANIFEST_UNKNOWN — for every image, old and new.
# Digest pulls (podman/containerd/kubelet) resolve fine, so Jobs may still be
# digest-pinned. Verify a push with: podman pull ...@sha256:<digest>.
#
# Build (on an aarch64 node, native — arm64 is the only runtime target):
#   scp -r llm-test/puller <node>:/tmp/puller-build
#   ssh <node> 'cd /tmp/puller-build && podman build \
#     -t registry.taildeab2.ts.net/homelab/model-cache-puller:v7 . && \
#     podman push registry.taildeab2.ts.net/homelab/model-cache-puller:v7'
# Reference the image by an immutable digest in Jobs and bump the versioned tag
# on change.
#
# v7 (2026-11-18): REBRAND. Same code as glm53-cache-puller:v6 (puller.py
#   unchanged, sha256 fbad2c4d88eedccec40708fdce28d40b355766c7080a5d60f3c103990c77cc5a),
#   pushed under the generic name homelab/model-cache-puller. New Jobs use this
#   name; glm53-cache-puller:v6 stays as a live alias for existing pinned Jobs.

# v6 (2026-10-03): report persisted cache progress and effective interval /
# average throughput every PROGRESS_INTERVAL seconds (default 30).
#
# v5 (2026-09-13): preserve and byte-range-resume interrupted .part files.
#
# v4 (2026-09-13): PULL_MODELS specs gain an optional '#glob|glob' include
# filter for PARTIAL repo pulls (e.g. single shards of a large checkpoint).
# Backward compatible: specs without '#' behave exactly as v3. Full pulls still
# write refs/main; partial pulls deliberately do not. See puller.py docstring.
#
# Or build for the puller from a registry host. The serve/caching image
# (ghcr.io/miaai-lab/glm-5.3-flash-2x-dgx-sparks:exl3) is a SEPARATE image; this
# one is only the tool that populates the model cache volume.
FROM python:3.12-slim

RUN pip install --no-cache-dir \
        huggingface_hub \
        httpx \
        requests \
    && rm -rf /root/.cache/pip

COPY puller.py /opt/puller/puller.py

ENTRYPOINT ["python3", "/opt/puller/puller.py"]
