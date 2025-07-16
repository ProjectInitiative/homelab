# Stage 1: The Nix Builder
FROM nixos/nix:latest
WORKDIR /build

# Copy the Nix expression and the script into the builder
COPY ./init-tools.nix ./init-script.sh ./

# Build the derivation. This creates a symlink named 'result'
# pointing to our environment in the /nix/store.
RUN nix-build init-tools.nix -o result

RUN mkdir /pkcs11-store
# 2. Tell the tpm2-pkcs11 tools to use this directory.
ENV TPM2_PKCS11_STORE=/pkcs11-store
# ---------------------------

# Set the PATH to include the /bin directory of our new environment.
ENV PATH=/build/result/bin:${PATH}

# Set the default entrypoint to be our initialization script.
ENTRYPOINT [ "init-script" ]
