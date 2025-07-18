#!/bin/sh
set -e

MODULE_PATH="@tpm_pkcs11_lib@"
SOFTHSM2_MODULE_PATH="@softhsm2_lib@"
STORE_DIR="${STORE_DIR:?STORE_DIR environment variable not set}"

SOFTHSM2_CONF="${STORE_DIR}/softhsm2.conf"
SOFTHSM2_TOKEN_DIR="${STORE_DIR}/softhsm_token"
SEALED_PIN_PATH="${STORE_DIR}/softhsm_pin.sealed"
PCR_SELECTION="sha256:0,1,2,3,4,5,6,7"

SO_PIN="${SO_PIN:?SO_PIN environment variable not set}"
USER_PIN="${USER_PIN:?USER_PIN environment variable not set}"
TOKEN_NAME="${TOKEN_NAME:?TOKEN_NAME environment variable not set}"
KEY_LABEL="${KEY_LABEL:?KEY_LABEL environment variable not set}"
KEY_ID="${KEY_ID:?KEY_ID environment variable not set}"

FAPI_PROFILE_DIR="${FAPI_PROFILE_DIR:?FAPI_PROFILE_DIR environment variable not set}"
# FAPI_SYSTEM_DIR="${FAPI_SYSTEM_DIR:?FAPI_SYSTEM_DIR environment variable not set}"
# 
# --- FAPI Profile Handling ---
if [ -d "$FAPI_PROFILE_DIR" ] && [ "$(ls -A $FAPI_PROFILE_DIR)" ]; then
    echo "✅ FAPI profiles already exist in the shared volume."
else
    echo "Creating FAPI profiles directory..."
    echo "Searching for FAPI profiles in /nix/store..."
    PROFILE_SRC_DIR=$(find /nix/store -name "fapi-profiles" -type d | head -n 1)

    if [ -z "$PROFILE_SRC_DIR" ]; then
      echo "❌ FAPI profiles directory not found in Nix store. This is unexpected."
      exit 1
    fi

    echo "Found FAPI profiles at: $PROFILE_SRC_DIR"
    echo "Copying profiles to shared volume at $FAPI_PROFILE_DIR..."
    mkdir -p "$FAPI_PROFILE_DIR"
    cp -rT "$PROFILE_SRC_DIR" "$FAPI_PROFILE_DIR"
    echo "✅ Profiles copied successfully."
fi

# --- Provision FAPI ---
echo "Checking FAPI provisioning status..."
# Temporarily disable exit-on-error to inspect the command's output
set +e
provision_output=$(tss2_provision 2>&1)
provision_exit_code=$?
set -e # Re-enable exit-on-error

if [ ${provision_exit_code} -eq 0 ]; then
    echo "✅ FAPI provisioning successful."
elif echo "${provision_output}" | grep -q "Already provisioned"; then
    echo "✅ FAPI was already provisioned."
else
    # This is a real, unexpected error.
    echo "❌ FAPI provisioning failed with a fatal error:"
    echo "${provision_output}"
    exit ${provision_exit_code}
fi

echo "Checking TPM token status..."
if pkcs11-tool --module "${MODULE_PATH}" --list-slots | grep -q 'token initialized'; then
  echo "✅ TPM token is already initialized."
else
  echo "⚠️ TPM token not initialized. Initializing now..."
  pkcs11-tool --module "${MODULE_PATH}" --init-token --so-pin="${SO_PIN}" --label="${TOKEN_NAME}"
  pkcs11-tool --module "${MODULE_PATH}" --init-pin --so-pin="${SO_PIN}" --pin="${USER_PIN}"
  echo "✅ Initialization complete."
fi

# --- SoftHSM Initialization with Ephemeral PIN ---
mkdir -p "${SOFTHSM2_TOKEN_DIR}"
if [ ! -f "${SOFTHSM2_CONF}" ]; then
    echo "⚠️ SoftHSM config not found. Creating new one."
    echo "objectstore.backend = file" > "${SOFTHSM2_CONF}"
    echo "directories.tokendir = ${SOFTHSM2_TOKEN_DIR}" >> "${SOFTHSM2_CONF}"
fi
export SOFTHSM2_CONF

# This is the key change: Generate a random PIN instead of using an env var.
GENERATED_PIN=$(openssl rand -base64 32)

if ! softhsm2-util --show-slots | grep -q "Slot 0"; then
    echo "⚠️ SoftHSM token not found. Initializing with a newly generated ephemeral PIN."
    softhsm2-util --init-token --slot 0 --label "${TOKEN_NAME}" --so-pin "${SO_PIN}" --pin "${GENERATED_PIN}"
else
    echo "✅ SoftHSM token already initialized."
fi

# --- Seal the Ephemeral PIN with the TPM ---
if [ ! -f "${SEALED_PIN_PATH}" ]; then
    # echo "⚠️ Sealed SoftHSM PIN not found. Sealing the newly generated PIN with TPM."
    # tpm2_createprimary -C o -c primary.ctx
    # tpm2_createpolicy --policy-pcr -l "${PCR_SELECTION}" -L policy.pcr
    # # Seal the GENERATED_PIN.
    # echo -n "${GENERATED_PIN}" | tpm2_create -C primary.ctx -L policy.pcr -i- -c sealed.key.ctx -u sealed.key.pub
    # tpm2_load -C primary.ctx -c sealed.key.ctx -u sealed.key.pub -r- > "${SEALED_PIN_PATH}"
    # rm -f primary.ctx policy.pcr sealed.key.ctx sealed.key.pub
    # echo "✅ Ephemeral SoftHSM PIN sealed successfully."
    echo "⚠️ Sealed SoftHSM PIN not found. Sealing the newly generated PIN with TPM."
    tpm2_createprimary -C o -c primary.ctx
    # The PIN is now sealed directly to the primary key without a PCR policy.
    echo -n "${GENERATED_PIN}" | tpm2_create -C primary.ctx -i- -c sealed.key.ctx -u sealed.key.pub
    tpm2_load -C primary.ctx -c sealed.key.ctx -u sealed.key.pub -r- > "${SEALED_PIN_PATH}"
    rm -f primary.ctx sealed.key.ctx sealed.key.pub
    echo "✅ Ephemeral SoftHSM PIN sealed successfully."
else
    echo "✅ Sealed SoftHSM PIN already exists."
fi

# --- Generate the final Unseal Key in SoftHSM ---
echo "Checking for the unseal key in SoftHSM..."
  if ! pkcs11-tool --module "${SOFTHSM2_MODULE_PATH}" --list-objects --login --pin "${GENERATED_PIN}" | grep -q "label: ${KEY_LABEL}"; then
    echo "⚠️ Unseal key not found in SoftHSM. Generating now."
    pkcs11-tool --module "${SOFTHSM2_MODULE_PATH}" \
      --login --pin "${GENERATED_PIN}" \
      --keypairgen --key-type rsa:2048 \
      --label "${KEY_LABEL}"
    echo "✅ Unseal key generated in SoftHSM successfully."
else
    echo "✅ Unseal key already exists in SoftHSM."
fi

# The GENERATED_PIN is now out of scope and disappears.
echo "✅ Initialization complete."

exit 0
