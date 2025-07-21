#!/bin/bash
# Copyright (c) HashiCorp, Inc.
# SPDX-License-Identifier: MPL-2.0
#
# Modifications made to integrate TPM-based auto-unsealing of a SoftHSM token
# and to allow for executing ad-hoc 'bao' commands.

set -e

# --- [ENTRYPOINT DEBUG] ---
echo "--- [ENTRYPOINT DEBUG] Received arguments: [$*] ---" >&2
# --- END DEBUG ---

# Prevent core dumps
ulimit -c 0

# Ensure TSS2_TCTI is set for all TPM commands
TSS2_TCTI="${TSS2_TCTI:?TSS2_TCTI environment variable not set}"
export TSS2_TCTI

echo "--- Preparing Environment as root ---"
# Only run chown if we are root
if [ "$(id -u)" = '0' ]; then
    echo "Changing ownership of writeable data directories..."
    chown -R openbao:openbao /openbao/data /openbao/logs /pkcs11-store
fi
echo "--- Environment preparation complete ---"


# Initialize variables
EXEC_CMD=("$@")
UNSEALED_PIN=""

# --- Integration Point: Always attempt TPM Unsealing Logic ---
# This logic now runs for any 'bao' command, not just 'bao server'.
if [ "$1" = 'bao' ]; then
    echo "--- [UNSEAL LOGIC] 'bao' command detected. Attempting to unseal SoftHSM PIN from TPM... ---"
    
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

# Prepare the environment with the unsealed PIN if available
if [ -n "${UNSEALED_PIN}" ]; then
    echo "✅ Exporting BAO_HSM_PIN for the upcoming command."
    export BAO_HSM_PIN="${UNSEALED_PIN}"
    export SOFTHSM2_CONF
fi

if [ "$(id -u)" = '0' ] && [ -z "$BAO_SKIP_DROP_ROOT" ]; then
    # We are root, drop to the 'openbao' user
    echo "✅ Executing as 'openbao' user."
    exec su-exec openbao "${EXEC_CMD[@]}"
else
    # We are not root, execute as the current user
    echo "✅ Executing as current user."
    exec "${EXEC_CMD[@]}"
fi
