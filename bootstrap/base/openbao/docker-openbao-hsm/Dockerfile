FROM nixos/nix:latest AS build

WORKDIR /build

COPY openbao.nix entrypoint.sh ./

# Create a group for the TPM device (e.g., tss) and add the openbao user to it.
# You may need to change the group name and GID to match your host system.
RUN echo "tss:x:104:openbao" >> /etc/group && \
    echo "openbao:x:1000:104::/home/openbao:/bin/sh" >> /etc/passwd

RUN nix-build openbao.nix

RUN mkdir -p ./output/store
RUN cp -va $(nix-store -qR ./result) ./output/store/

RUN mkdir -p ./output/openbao/config ./output/openbao/file ./output/openbao/logs


FROM scratch

# Copy the Nix store and the environment from the build stage.
COPY --from=build /build/output/store/ /nix/store/
COPY --from=build /build/result /root/env

# Copy the user/group files that now include the 'openbao' user in the 'tss' group.
COPY --from=build /etc/passwd /etc/passwd
COPY --from=build /etc/group /etc/group

# Copy the openbao directories.
COPY --from=build /build/output/openbao /openbao

ENV PATH=/root/env/bin

ENTRYPOINT ["entrypoint.sh"]