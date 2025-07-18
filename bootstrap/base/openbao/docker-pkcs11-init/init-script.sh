#!/bin/sh
set -e

MODULE_PATH="@tpm_pkcs11_lib@"
SO_PIN="${SO_PIN:?SO_PIN environment variable not set}"
USER_PIN="${USER_PIN:?USER_PIN environment variable not set}"
TOKEN_NAME="${TOKEN_NAME:?TOKEN_NAME environment variable not set}"

FAPI_PROFILE_DIR="${FAPI_PROFILE_DIR:?FAPI_PROFILE_DIR environment variable not set}"
# FAPI_SYSTEM_DIR="${FAPI_SYSTEM_DIR:?FAPI_SYSTEM_DIR environment variable not set}"

echo "Checking TPM token status..."
if pkcs11-tool --module "${MODULE_PATH}" --list-slots | grep -q 'token initialized'; then
  echo "✅ TPM token is already initialized."
else
  echo "⚠️ TPM token not initialized. Initializing now..."
  pkcs11-tool --module "${MODULE_PATH}" --init-token --so-pin="${SO_PIN}" --label="${TOKEN_NAME}"
  pkcs11-tool --module "${MODULE_PATH}" --init-pin --so-pin="${SO_PIN}" --pin="${USER_PIN}"
  echo "✅ Initialization complete."
fi

# --- FAPI Profile Handling ---
if [ -d "$FAPI_PROFILE_DIR" ] && [ "$(ls -A $FAPI_PROFILE_DIR)" ]; then
    echo "✅ FAPI profiles already exist in the shared volume."
else
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


exit 0
