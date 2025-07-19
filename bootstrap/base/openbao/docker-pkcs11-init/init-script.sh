#!/bin/sh

set -e
set -o pipefail

MODULE_PATH="@tpm_pkcs11_lib@"
SOFTHSM2_MODULE_PATH="@softhsm2_lib@"

STORE_DIR="$TPM2_PKCS11_STORE"
SOFTHSM2_CONF="${STORE_DIR}/softhsm2.conf"
SOFTHSM2_TOKEN_DIR="${STORE_DIR}/softhsm_token"

PRIMARY_CTX_PATH="${STORE_DIR}/primary.ctx"
SEALED_PIN_PUB_PATH="${STORE_DIR}/softhsm_pin.pub"
SEALED_PIN_PRIV_PATH="${STORE_DIR}/softhsm_pin.priv"

SO_PIN="${SO_PIN:?SO_PIN environment variable not set}"
USER_PIN="${USER_PIN:?USER_PIN environment variable not set}"
TOKEN_NAME="${TOKEN_NAME:?TOKEN_NAME environment variable not set}"
KEY_LABEL="${KEY_LABEL:?KEY_LABEL environment variable not set}"
FAPI_PROFILE_DIR="${FAPI_PROFILE_DIR:?FAPI_PROFILE_DIR environment variable not set}"

TSS2_TCTI="${TSS2_TCTI:?TSS2_TCTI environment variable not set}"
export TSS2_TCTI

# --- THE MAIN LOGIC: All or Nothing ---
# If the final artifact (the sealed PIN) already exists, our work is done.
if [ -f "${SEALED_PIN_PRIV_PATH}" ]; then
    echo "✅ Initialization artifacts already exist. Nothing to do."
    exit 0
fi

# --- If we are here, it means we are performing a full, first-time initialization ---
echo "⚠️ No existing initialization found. Performing full setup..."

# --- 1. FAPI and TPM Token Setup (Idempotent, safe to run again) ---
# FAPI Profile Handling
if [ ! -d "$FAPI_PROFILE_DIR" ] || [ -z "$(ls -A "$FAPI_PROFILE_DIR")" ]; then
    echo "Creating FAPI profiles directory..."
    PROFILE_SRC_DIR=$(find /nix/store -name "fapi-profiles" -type d | head -n 1)
    if [ -z "$PROFILE_SRC_DIR" ]; then echo "❌ FAPI profiles not found." && exit 1; fi
    mkdir -p "$FAPI_PROFILE_DIR" && cp -rT "$PROFILE_SRC_DIR" "$FAPI_PROFILE_DIR"
    echo "✅ FAPI profiles copied."
fi

# FAPI Provisioning
echo "Checking FAPI provisioning status..."
set +e
provision_output=$(tss2_provision 2>&1) && provision_exit_code=$? || provision_exit_code=$?
set -e
if [ ${provision_exit_code} -eq 0 ]; then
    echo "✅ FAPI provisioning successful."
elif echo "${provision_output}" | grep -q "Already provisioned"; then
    echo "✅ FAPI was already provisioned."
else
    echo "❌ FAPI provisioning failed:" && echo "${provision_output}" && exit ${provision_exit_code}
fi

# TPM Token Initialization
# if ! pkcs11-tool --module "${MODULE_PATH}" --list-slots | grep -q 'token initialized'; then
#     echo "Initializing TPM PKCS#11 token..."
#     pkcs11-tool --module "${MODULE_PATH}" --init-token --so-pin="${SO_PIN}" --label="${TOKEN_NAME}"
#     pkcs11-tool --module "${MODULE_PATH}" --init-pin --so-pin="${SO_PIN}" --pin="${USER_PIN}"
#     echo "✅ TPM token initialized."
# else
#     echo "✅ TPM token already initialized."
# fi

# --- 2. SoftHSM Setup from Scratch ---
echo "Initializing SoftHSM..."
mkdir -p "${SOFTHSM2_TOKEN_DIR}"
echo "objectstore.backend = file" > "${SOFTHSM2_CONF}"
echo "directories.tokendir = ${SOFTHSM2_TOKEN_DIR}" >> "${SOFTHSM2_CONF}"
export SOFTHSM2_CONF

# Generate a single-use ephemeral PIN for this initialization run.
GENERATED_PIN=$(openssl rand -base64 32)

# Initialize a new SoftHSM token with our generated PIN.
softhsm2-util --init-token --free --label "${TOKEN_NAME}" --so-pin "${SO_PIN}" --pin "${GENERATED_PIN}"
echo "✅ SoftHSM token initialized."

# --- 3. Seal the PIN and Generate the Final Key ---
echo "Sealing the ephemeral SoftHSM PIN with the TPM..."
tpm2_createprimary -T "${TSS2_TCTI}" -C o -c "${PRIMARY_CTX_PATH}" \
    || { echo "❌ ERROR: tpm2_createprimary failed."; exit 1; }

echo -n "${GENERATED_PIN}" | tpm2_create \
    -T "${TSS2_TCTI}" \
    -C "${PRIMARY_CTX_PATH}" -i- \
    -u "${SEALED_PIN_PUB_PATH}" -r "${SEALED_PIN_PRIV_PATH}" \
    || { echo "❌ ERROR: tpm2_create failed to seal the PIN."; exit 1; }
echo "✅ Ephemeral PIN sealed successfully."

# Find the newly created slot
SLOT_ID=$(softhsm2-util --show-slots | awk -v token="${TOKEN_NAME}" '/^Slot/ {slot=$2} $0 ~ "Label:[[:space:]]*" token {print slot}')
if [ -z "$SLOT_ID" ]; then echo "❌ Could not find the new SoftHSM slot." && exit 1; fi
echo "✅ Found new token in slot ${SLOT_ID}."

# Generate the final unseal key inside SoftHSM, using the same ephemeral PIN.
echo "Generating the final unseal key in SoftHSM..."
pkcs11-tool --module "${SOFTHSM2_MODULE_PATH}" \
  --slot "${SLOT_ID}" \
  --login --pin "${GENERATED_PIN}" \
  --keypairgen --key-type rsa:2048 \
  --label "${KEY_LABEL}" \
  || { echo "❌ ERROR: Failed to generate unseal key in SoftHSM."; exit 1; }
echo "✅ Unseal key generated successfully."

# The GENERATED_PIN now goes out of scope and is forgotten.
echo "✅ Initialization complete."

exit 0
