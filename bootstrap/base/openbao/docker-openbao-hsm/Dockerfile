# =================================================================
# BUILD STAGE
# =================================================================
FROM nixos/nix:latest AS build

WORKDIR /build

# MODIFIED: Copy the new shim files along with the existing ones
COPY openbao.nix entrypoint.sh shim.nix shim.sh ./

# Create the openbao group, and the tss group with the openbao user.
# Then create the openbao user with its primary group set to openbao.
# YOU MUST REPLACE 985 WITH THE GID FROM YOUR HOST SYSTEM.
RUN echo "openbao:x:1000:" >> /etc/group && \
    echo "tss:x:995:openbao" >> /etc/group && \
    echo "openbao:x:1000:1000::/home/openbao:/bin/sh" >> /etc/passwd

# Create and set ownership for the required directories.
RUN mkdir -p /home/openbao /pkcs11-store && \
    chown -R openbao:openbao /home/openbao /pkcs11-store

# Build the main openbao derivation
RUN nix-build openbao.nix

# NEW: Build the shim derivation and create a symlink named 'shim-result' for easy access
RUN nix-build shim.nix -o shim-result

# Collect the Nix store paths for the final image
RUN mkdir -p ./output/store

# MODIFIED: Collect the full dependency closure for BOTH derivations ('result' and 'shim-result')
RUN cp -va $(nix-store -qR ./result ./shim-result) ./output/store/

RUN mkdir -p ./output/openbao/config ./output/openbao/file ./output/openbao/logs


# =================================================================
# FINAL STAGE
# =================================================================
FROM scratch

# Copy the Nix store (now containing both openbao and the shim's dependencies)
COPY --from=build /build/output/store/ /nix/store/
# Copy the result of the main openbao build to populate the environment
COPY --from=build /build/result /root/env

# Copy the /usr directory from the build result to the root of the final image.
COPY --from=build /build/result/usr /usr

# Copy the user/group files that now include the 'openbao' user and group.
COPY --from=build /etc/passwd /etc/passwd
COPY --from=build /etc/group /etc/group

# Copy the created directories.
COPY --from=build /home/openbao /home/openbao
COPY --from=build /pkcs11-store /pkcs11-store

# Copy the openbao directories.
COPY --from=build /build/output/openbao /openbao

# NEW: Copy the compiled shim and place it at /bin/sh in the final image.
# This makes it the default shell.
COPY --from=build /build/shim-result/bin/sh /bin/sh

# The PATH allows the shim to find the original 'entrypoint.sh' (assuming it's in result/bin)
ENV PATH=/root/env/bin
ENV TPM2_PKCS11_STORE=/pkcs11-store
ENV TSS2_FAPICONF=/config/fapi-config.json

# MODIFIED: Change the entrypoint to the shim.
# When a Helm chart runs a command like `sh -c "bao status"`, our shim at /bin/sh will
# intercept it and delegate to the original 'entrypoint.sh' script.
ENTRYPOINT ["/bin/sh"]
