#!/usr/bin/env bash
# Build the Flare serving image from the pinned upstream revision.
#
# The upstream Dockerfile is a two-stage Rust build producing a minimal
# runtime image (flare binary + RoCE userland only). We wrap it so the
# pinned source revision is cloned exactly, then delegate to it verbatim.
set -euo pipefail

FLARE_REV=5f37bd14062334f7687d168d58ea00567b9aa7fe
IMAGE=${1:-registry.taildeab2.ts.net/homelab/flare-runtime:5f37bd1}

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
git clone --filter=blob:none https://github.com/NVIDIA/flare-local-inference.git "$work/src"
git -C "$work/src" checkout --detach "$FLARE_REV"

docker build --platform linux/arm64 -t "$IMAGE" "$work/src"
echo "built $IMAGE from $FLARE_REV"
