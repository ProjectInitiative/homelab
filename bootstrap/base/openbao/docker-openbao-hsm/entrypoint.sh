#!/bin/bash
# Copyright (c) HashiCorp, Inc.
# SPDX-License-Identifier: MPL-2.0
#
# Modifications made to integrate TPM-based auto-unsealing of a SoftHSM token.

set -e

# --- [ENTRYPOINT DEBUG] ---
echo "--- [ENTRYPOINT DEBUG] Received arguments: [$1] [$2] [$3] ---" >&2
# --- END DEBUG ---

# Prevent core dumps
ulimit -c 0

# Ensure TSS2_TCTI is set for all TPM commands
TSS2_TCTI="${TSS2_TCTI:?TSS2_TCTI environment variable not set}"
export TSS2_TCTI

echo "--- Preparing Environment as root ---"
echo "Changing ownership of writeable data directories..."
chown -R openbao:openbao /openbao/data /openbao/logs /pkcs11-store
echo "--- Environment preparation complete ---"


# Initialize variables
EXEC_CMD=("$@")
UNSEALED_PIN=""

# --- Integration Point: TPM Unsealing Logic ---
if [ "$1" = 'bao' ] && [ "$2" = 'server' ]; then
    echo "--- [UNSEAL LOGIC] Condition met. Attempting to unseal SoftHSM PIN from TPM... ---"
    
    # THE FIX: Re-added the missing command to ensure /tmp exists.
    mkdir -p /tmp
    
    STORE_DIR="${TPM2_PKCS11_STORE:?TPM2_PKCS11_STORE variable not set}"
    PRIMARY_CTX_PATH="${STORE_DIR}/primary.ctx"
    SEALED_PIN_PUB_PATH="${STORE_DIR}/softhsm_pin.pub"
    SEALED_PIN_PRIV_PATH="${STORE_DIR}/softhsm_pin.priv"
    SEALED_CTX_PATH="/tmp/sealed.ctx"
    trap 'rm -f "${SEALED_CTX_PATH}"' EXIT

    if [ ! -f "${PRIMARY_CTX_PATH}" ] || [ ! -f "${SEALED_PIN_PUB_PATH}" ] || [ ! -f "${SEALED_PIN_PRIV_PATH}" ]; then
        echo "❌ ERROR: One or more required TPM sealed object files not found in ${STORE_DIR}."
        exit 1
    fi
    echo "✅ Found all necessary TPM sealed object files."

    echo "Loading sealed object into TPM..."
    tpm2_load -T "${TSS2_TCTI}" -C "${PRIMARY_CTX_PATH}" -u "${SEALED_PIN_PUB_PATH}" -r "${SEALED_PIN_PRIV_PATH}" -c "${SEALED_CTX_PATH}" \
        || { echo "❌ ERROR: tpm2_load failed." && exit 1; }
    echo "✅ Sealed object loaded."

    echo "Unsealing PIN..."
    UNSEALED_PIN=$(tpm2_unseal -T "${TSS2_TCTI}" -c "${SEALED_CTX_PATH}")

    if [ -z "${UNSEALED_PIN}" ]; then
        echo "❌ ERROR: tpm2_unseal failed or produced an empty PIN." && exit 1
    fi
    echo "✅ PIN unsealed successfully."
fi


# --- Final, Secure Execution ---
echo "Starting OpenBao process..."
SOFTHSM2_CONF="/pkcs11-store/softhsm2.conf"

if [ "$(id -u)" = '0' ] && [ -z "$BAO_SKIP_DROP_ROOT" ]; then
    if [ -n "${UNSEALED_PIN}" ]; then
        echo "✅ Executing as 'openbao' user with the unsealed PIN."
        exec su-exec openbao env \
            SOFTHSM2_CONF="${SOFTHSM2_CONF}" \
            BAO_HSM_PIN="${UNSEALED_PIN}" \
            "${EXEC_CMD[@]}"
    else
        echo "❌ Executing as 'openbao' user WITHOUT the unsealed PIN. This will fail if seal is pkcs11."
        exec su-exec openbao "${EXEC_CMD[@]}"
    fi
else
    if [ -n "${UNSEALED_PIN}" ]; then
        echo "✅ Executing as current user with the unsealed PIN."
        exec env \
            SOFTHSM2_CONF="${SOFTHSM2_CONF}" \
            BAO_HSM_PIN="${UNSEALED_PIN}" \
            "${EXEC_CMD[@]}"
    else
        echo "❌ Executing as current user WITHOUT the unsealed PIN. This will fail if seal is pkcs11."
        exec "${EXEC_CMD[@]}"
    fi
fi
