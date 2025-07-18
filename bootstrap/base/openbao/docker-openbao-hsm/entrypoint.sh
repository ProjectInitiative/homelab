#!/bin/bash
# Copyright (c) HashiCorp, Inc.
# SPDX-License-Identifier: MPL-2.0
#
# Modifications made to integrate TPM-based auto-unsealing of a SoftHSM token.

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

# --- Argument parsing to determine the command ---
if [ "${1:0:1}" = '-' ]; then
    set -- bao "$@"
fi

# This is the command that will be executed in the final, clean environment
EXEC_CMD=("$@")
UNSEALED_PIN=""

# --- Integration Point: TPM Unsealing Logic ---
# This logic will only run if the command is "server".
if [ "$1" = 'server' ]; then
    echo "Unsealing SoftHSM PIN from TPM..."

    # Configuration for our hybrid setup
    STORE_DIR="/pkcs11-store"
    SEALED_PIN_PATH="${STORE_DIR}/softhsm_pin.sealed"
    PCR_SELECTION="sha256:0,1,2,3,4,5,6,7"

    # Ensure /tmp exists
    mkdir -p /tmp

    # The TPM will only succeed if the PCR state matches.
    UNSEALED_PIN=$(tpm2_unseal -c "${SEALED_PIN_PATH}" -p pcr:"${PCR_SELECTION}")

    echo "PIN unsealed successfully."

    # --- Construct the final 'bao server' command ---
    shift
    EXEC_CMD=(bao server -config="$BAO_CONFIG_DIR" "$@")

elif [ "$1" = 'version' ]; then
    : # Do nothing for version command
elif bao --help "$1" 2>&1 | grep -q "bao $1"; then
    : # Do nothing for other valid bao commands
fi


# --- Original OpenBao chown logic ---
if [ "$1" = 'bao' ]; then
    if [ -z "$SKIP_CHOWN" ]; then
        if [ -d "/openbao/config" ] && [ "$(stat -c %u /openbao/config)" != "$(id -u openbao)" ]; then
            chown -R openbao:openbao /openbao/config || echo "Could not chown /openbao/config"
        fi
        if [ -d "/openbao/data" ] && [ "$(stat -c %u /openbao/data)" != "$(id -u openbao)" ]; then
            chown -R openbao:openbao /openbao/data
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
        if [ -d "/pkcs11-store" ] && [ "$(stat -c %u /pkcs11-store)" != "$(id -u openbao)" ]; then
            chown -R openbao:openbao /pkcs11-store
        fi
    fi
fi

# --- Final, Secure Execution ---
echo "Starting OpenBao process with minimal environment..."

if [ "$(id -u)" = '0' ] && [ -z "$BAO_SKIP_DROP_ROOT" ]; then
    # Drop root privileges AND create a clean environment for the final command
    if [ -n "${UNSEALED_PIN}" ]; then
        # If we unsealed a PIN, run the server with it in the environment.
        exec su-exec openbao env BAO_HSM_PIN="${UNSEALED_PIN}" "${EXEC_CMD[@]}"
    else
        # Otherwise, run the command without the PIN (e.g., 'bao operator init').
        exec su-exec openbao "${EXEC_CMD[@]}"
    fi
else
    # If not running as root, execute directly
    if [ -n "${UNSEALED_PIN}" ]; then
        exec env BAO_HSM_PIN="${UNSEALED_PIN}" "${EXEC_CMD[@]}"
    else
        exec "${EXEC_CMD[@]}"
    fi
fi
