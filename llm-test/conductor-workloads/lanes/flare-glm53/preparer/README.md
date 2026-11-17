# Flare Ignition preparation image

This image is the build-time/compiler side of Flare. It is intentionally
separate from `flare-runtime`.

It contains the pinned Flare source, Ignition, Python 3.12, CUDA 13.2,
PyTorch, FlashInfer, and the native preparation toolchain. It must run with
GPU access and writes a prepared package to a caller-mounted workspace or
shared model-cache path.

The image does not contain model weights or signing private keys. Inputs,
outputs, trust material, and the exact `ignition export` arguments are supplied
by the typed Conductor preparation workflow. The output is not consumable until
its manifest and trust/receipt checks pass.

Build identity:

- Flare source: `5f37bd14062334f7687d168d58ea00567b9aa7fe`
- CUDA base: `nvcr.io/nvidia/cuda:13.2.0-devel-ubuntu24.04`
- Base architecture: Linux arm64

The serving image remains a separate small image that contains only Flare and
its runtime libraries.
