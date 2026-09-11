# Generic Hugging Face cache puller / deleter image.
#
# Minimal, model-agnostic. Only needs Python + huggingface_hub + requests.
# Pulls are rate-limited *in code* (token bucket on the HTTP session), so no
# tc/iproute2 is required in the image - throttling is fully controllable via
# the RATE parameter at job time.
#
# Build (on an aarch64 node, native):
#   podman build -t registry.taildeab2.ts.net/homelab/glm53-cache-puller:v1 .
#   podman push registry.taildeab2.ts.net/homelab/glm53-cache-puller:v1
# Reference the image by a versioned tag (e.g. :v1) in the Job and bump it on
# change; digest pinning against this registry is unreliable (the registry stores
# a different manifest digest than the local build).
#
# Or build for the puller from a registry host. The serve/caching image
# (ghcr.io/miaai-lab/glm-5.3-flash-2x-dgx-sparks:exl3) is a SEPARATE image; this
# one is only the tool that populates the model cache volume.
FROM python:3.12-slim

RUN pip install --no-cache-dir \
        huggingface_hub \
        requests \
    && rm -rf /root/.cache/pip

COPY puller.py /opt/puller/puller.py

ENTRYPOINT ["python3", "/opt/puller/puller.py"]
