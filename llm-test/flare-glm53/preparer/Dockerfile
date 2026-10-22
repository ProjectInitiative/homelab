# syntax=docker/dockerfile:1
# Flare Ignition preparation image. This is deliberately separate from the
# production flare-runtime image: preparation needs Python, PyTorch, CUDA,
# FlashInfer, compilers, and the pinned Flare source tree.
ARG CUDA_BASE_DIGEST=sha256:a5b6256e470196fc1d5f8f62139d57d3662867746dfe1cb352d7652024047020
FROM nvcr.io/nvidia/cuda:13.2.0-devel-ubuntu24.04@${CUDA_BASE_DIGEST}

ARG FLARE_REV=5f37bd14062334f7687d168d58ea00567b9aa7fe
ARG UV_VERSION=0.11.21
ARG RUST_VERSION=1.94.1

ENV DEBIAN_FRONTEND=noninteractive \
    UV_NO_CACHE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/flare/.venv \
    PATH=/opt/flare/.venv/bin:/opt/flare/flare/target/release:/root/.cargo/bin:$PATH \
    CUDA_HOME=/usr/local/cuda

RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential ca-certificates cmake curl git libibverbs-dev \
      libjpeg-dev libssl-dev liburing-dev nasm pkg-config protobuf-compiler \
      python3.12 python3.12-dev python3.12-venv \
    && rm -rf /var/lib/apt/lists/* \
    && curl --proto '=https' --tlsv1.2 -LsSf "https://astral.sh/uv/${UV_VERSION}/install.sh" | sh \
    && curl --proto '=https' --tlsv1.2 https://sh.rustup.rs | sh -s -- -y --default-toolchain "${RUST_VERSION}" --profile minimal \
    && rustup component add rustfmt

WORKDIR /opt/flare
RUN git clone --filter=blob:none https://github.com/NVIDIA/flare-local-inference.git . \
    && git checkout --detach "${FLARE_REV}" \
    && git config --global --add safe.directory /opt/flare

# Installs the exact locked preparation graph, including the local Heliopause
# extension and CUDA/PyTorch/FlashInfer dependencies.
RUN uv sync --locked --extra prepare \
    && cargo build --locked --release --manifest-path flare/Cargo.toml --bin flare

COPY entrypoint.sh /usr/local/bin/flare-ignition-prep
RUN chmod 0755 /usr/local/bin/flare-ignition-prep

WORKDIR /workspace
ENTRYPOINT ["/usr/local/bin/flare-ignition-prep"]
