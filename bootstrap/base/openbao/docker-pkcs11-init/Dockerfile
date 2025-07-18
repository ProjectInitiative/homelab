FROM nixos/nix:latest AS build

# Set a working directory.
WORKDIR /build

COPY ./init-tools.nix ./init-script.sh ./

# Build the Nix expression.
RUN nix-build init-tools.nix

# Calculate and copy the Nix closure.
RUN mkdir -p ./output/store
RUN cp -va $(nix-store -qR ./result) ./output/store/

# Create any required directories in the builder stage.
RUN mkdir ./pkcs11-store
RUN mkdir ./pkcs11-store/fapi-profiles

# # This stage assembles the minimal components into an empty image.
FROM scratch

# Copy the Nix closure and the profile.
COPY --from=build /build/output/store/ /nix/store/
COPY --from=build /build/result/ /

# Copy user/group files.
COPY --from=build /etc/passwd /etc/passwd
COPY --from=build /etc/group /etc/group

# Copy the pre-made directory from the builder instead of trying to RUN mkdir.
COPY --from=build /build/pkcs11-store /pkcs11-store

# Set environment variables.
ENV TPM2_PKCS11_STORE=/pkcs11-store

ENV FAPI_PROFILE_DIR=/pkcs11-store/fapi-profiles

ENV TSS2_FAPICONF=/config/fapi-config.json

ENV PATH=/bin

# Set the entrypoint.
ENTRYPOINT [ "init-script" ]
