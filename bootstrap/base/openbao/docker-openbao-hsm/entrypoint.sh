#!/bin/bash
# Copyright (c) HashiCorp, Inc.
# SPDX-License-Identifier: MPL-2.0
#
# Modifications made to integrate TPM-based auto-unsealing of a SoftHSM token.

set -e

# Prevent core dumps
ulimit -c 0

# Ensure TSS2_TCTI is set for all TPM commands
TSS2_TCTI="${TSS2_TCTI:?TSS2_TCTI environment variable not set}"
export TSS2_TCTI

# --- FIX: Unconditional, Verbose Permission Fix ---
# This block runs every time, as root, before anything else.
# It guarantees that the 'openbao' user can read/write to all necessary
# directories, especially the /pkcs11-store created by the other container.
echo "--- Preparing Environment as root ---"
echo "Fixing permissions for /openbao/config..."
mkdir -p /openbao/config
chown -R openbao:openbao /openbao/config

echo "Fixing permissions for /openbao/data..."
mkdir -p /openbao/data
chown -R openbao:openbao /openbao/data

echo "Fixing permissions for /pkcs11-store..."
mkdir -p /pkcs11-store
chown -R openbao:openbao /pkcs11-store
echo "--- Environment preparation complete ---"


# Argument parsing to determine the command
if [ "${1:0:1}" = '-' ]; then
    set -- bao "$@"
fi

# This is the command that will be executed in the final, clean environment
EXEC_CMD=("$@")
UNSEALED_PIN=""

# --- Integration Point: TPM Unsealing Logic ---
if [ "$1" = 'server' ]; then
    echo "Attempting to unseal SoftHSM PIN from TPM..."
    mkdir -p /tmp
    STORE_DIR="${TPM2_PKCS11_STORE:?TPM2_PKCS11_STORE variable not set}"
    PRIMARY_CTX_PATH="${STORE_DIR}/primary.ctx"
    SEALED_PIN_PUB_PATH="${STORE_DIR}/softhsm_pin.pub"
    SEALED_PIN_PRIV_PATH="${STORE_DIR}/softhsm_pin.priv"
    SEALED_CTX_PATH="/tmp/sealed.ctx"
    trap 'rm -f "${SEALED_CTX_PATH}"' EXIT

    check_files_exist() {
        for file in "$@"; do
            if [ ! -f "$file" ]; then
                echo "❌ ERROR: Required unseal file not found: $file" && exit 1
            fi
        done
    }
    check_files_exist "${PRIMARY_CTX_PATH}" "${SEALED_PIN_PUB_PATH}" "${SEALED_PIN_PRIV_PATH}"
    echo "✅ Found all necessary TPM sealed object files."

    echo "Loading sealed object into TPM..."
    tpm2_load -T "${TSS2_TCTI}" -C "${PRIMARY_CTX_PATH}" -u "${SEALED_PIN_PUB_PATH}" -r "${SEALED_PIN_PRIV_PATH}" -c "${SEALED_CTX_PATH}" \
        || { echo "❌ ERROR: tpm2_load failed." && exit 1; }
    echo "✅ Sealed object loaded."

    echo "Unsealing PIN..."
    UNSEALED_PIN=$(tpm2_unseal -T "${TSS2_TCTI}" -c "${SEALED_CTX_PATH}")

    if [ -z "${UNSEALED_PIN}" ]; then echo "❌ ERROR: tpm2_unseal failed or produced empty PIN." && exit 1; fi
    echo "✅ PIN unsealed successfully."

    shift
    EXEC_CMD=(bao server -config="/openbao/config" "$@")
elif [ "$1" != "bao" ]; then
    EXEC_CMD=(bao "$@")
fi


# --- Final, Secure Execution ---
echo "Starting OpenBao process..."
SOFTHSM2_CONF="/pkcs11-store/softhsm2.conf"

if [ "$(id -u)" = '0' ] && [ -z "$BAO_SKIP_DROP_ROOT" ]; then
    if [ -n "${UNSEALED_PIN}" ]; then
        echo "Executing as 'openbao' user with the unsealed PIN."
        exec su-exec openbao env \
            SOFTHSM2_CONF="${SOFTHSM2_CONF}" \
            BAO_HSM_PIN="${UNSEALED_PIN}" \
            "${EXEC_CMD[@]}"
    else
        echo "Executing as 'openbao' user."
        exec su-exec openbao "${EXEC_CMD[@]}"
    fi
else
    if [ -n "${UNSEALED_PIN}" ]; then
        echo "Executing as current user with the unsealed PIN."
        exec env \
            SOFTHSM2_CONF="${SOFTHSM2_CONF}" \
            BAO_HSM_PIN="${UNSEALED_PIN}" \
            "${EXEC_CMD[@]}"
    else
        echo "Executing as current user."
        exec "${EXEC_CMD[@]}"
    fi
fi
