FROM nixos/nix:latest AS build

WORKDIR /build

COPY openbao.nix entrypoint.sh ./

# Create the openbao group, and the tss group with the openbao user.
# Then create the openbao user with its primary group set to openbao.
# YOU MUST REPLACE 995 WITH THE GID FROM YOUR HOST SYSTEM.
RUN echo "openbao:x:1000:" >> /etc/group && \
    echo "tss:x:995:openbao" >> /etc/group && \
    echo "openbao:x:1000:1000::/home/openbao:/bin/sh" >> /etc/passwd

# Create and set ownership for the required directories.
RUN mkdir -p /home/openbao /pkcs11-store && \
    chown -R openbao:openbao /home/openbao /pkcs11-store

RUN nix-build openbao.nix

RUN mkdir -p ./output/store
RUN cp -va $(nix-store -qR ./result) ./output/store/

RUN mkdir -p ./output/openbao/config ./output/openbao/file ./output/openbao/logs


FROM scratch

# Copy the Nix store and the environment from the build stage.
COPY --from=build /build/output/store/ /nix/store/
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

ENV PATH=/root/env/bin
ENV TPM2_PKCS11_STORE=/pkcs11-store
ENV TSS2_FAPICONF=/config/fapi-config.json

ENTRYPOINT ["entrypoint.sh"]
