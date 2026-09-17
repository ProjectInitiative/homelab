# Generic Hugging Face cache puller / deleter image.
#
# Minimal, model-agnostic. Only needs Python + huggingface_hub + requests.
# Pulls are rate-limited *in code* (token bucket on the HTTP session), so no
# tc/iproute2 is required in the image - throttling is fully controllable via
# the RATE parameter at job time.
#
# Build (on an aarch64 node, native):
#   podman build -t registry.taildeab2.ts.net/homelab/glm53-cache-puller:v5 .
#   podman push registry.taildeab2.ts.net/homelab/glm53-cache-puller:v5
# Reference the image by a versioned tag (e.g. :v5) in the Job and bump it on
# change. This private registry currently does not resolve Podman's reported
# digest through containerd, so Jobs use versioned tags with pullPolicy Always.
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
