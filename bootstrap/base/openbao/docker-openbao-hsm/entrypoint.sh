#!@dumb-init@ @shell@
# Copyright (c) HashiCorp, Inc.
# SPDX-License-Identifier: MPL-2.0

set -e

# Prevent core dumps
ulimit -c 0

# Allow setting BAO_REDIRECT_ADDR and BAO_CLUSTER_ADDR using an interface
# name instead of an IP address.
get_addr () {
    local if_name=$1
    local uri_template=$2
    ip addr show dev $if_name | awk -v uri=$uri_template '/\s*inet\s/ { \
      ip=gensub(/(.+)\/.+/, "\\1", "g", $2); \
      print gensub(/^(.+:\/\/).+(:.+)$/, "\\1" ip "\\2", "g", uri); \
      exit}'
}

if [ -n "$BAO_REDIRECT_INTERFACE" ]; then
    export BAO_REDIRECT_ADDR=$(get_addr $BAO_REDIRECT_INTERFACE ${BAO_REDIRECT_ADDR:-"http://0.0.0.0:8200"})
    echo "Using $BAO_REDIRECT_INTERFACE for BAO_REDIRECT_ADDR: $BAO_REDIRECT_ADDR"
fi
if [ -n "$BAO_CLUSTER_INTERFACE" ]; then
    export BAO_CLUSTER_ADDR=$(get_addr $BAO_CLUSTER_INTERFACE ${BAO_CLUSTER_ADDR:-"https://0.0.0.0:8201"})
    echo "Using $BAO_CLUSTER_INTERFACE for BAO_CLUSTER_ADDR: $BAO_CLUSTER_ADDR"
fi

BAO_CONFIG_DIR=/openbao/config

if [ -n "$BAO_LOCAL_CONFIG" ]; then
    echo "$BAO_LOCAL_CONFIG" > "$BAO_CONFIG_DIR/local.json"
fi

if [ "${1:0:1}" = '-' ]; then
    set -- bao "$@"
fi

if [ "$1" = 'server' ]; then
    shift
    set -- bao server \
        -config="$BAO_CONFIG_DIR" \
        -dev-root-token-id="$BAO_DEV_ROOT_TOKEN_ID" \
        -dev-listen-address="${BAO_DEV_LISTEN_ADDRESS:-"0.0.0.0:8200"}" \
        "$@"
elif [ "$1" = 'version' ]; then
    set -- bao "$@"
elif bao --help "$1" 2>&1 | grep -q "bao $1"; then
    set -- bao "$@"
fi

if [ "$1" = 'bao' ]; then
    if [ -z "$SKIP_CHOWN" ]; then
        if [ -d "/openbao/config" ] && [ "$(stat -c %u /openbao/config)" != "$(id -u openbao)" ]; then
            chown -R openbao:openbao /openbao/config || echo "Could not chown /openbao/config"
        fi
        if [ -d "/openbao/logs" ] && [ "$(stat -c %u /openbao/logs)" != "$(id -u openbao)" ]; then
            chown -R openbao:openbao /openbao/logs
        fi
        if [ -d "/openbao/file" ] && [ "$(stat -c %u /openbao/file)" != "$(id -u openbao)" ]; then
            chown -R openbao:openbao /openbao/file
        fi
        if [ -d "/home/openbao" ] && [ "$(stat -c %u /home/openbao)" != "$(id -u openbao)" ]; then
            chown -R openbao:openbao /home/openbao
        fi
        if [ -d "/var/lib/openbao-tpm" ] && [ "$(stat -c %u /var/lib/openbao-tpm)" != "$(id -u openbao)" ]; then
            chown -R openbao:openbao /var/lib/openbao-tpm
        fi
    fi

    if [ "$(id -u)" = '0' ] && [ -z "$BAO_SKIP_DROP_ROOT" ]; then
      set -- su-exec openbao "$@"
    fi
fi

exec "$@"