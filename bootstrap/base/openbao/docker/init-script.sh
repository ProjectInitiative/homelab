#!/bin/sh
set -e

# This placeholder will be replaced by Nix with the real library path.
MODULE_PATH="@tpm_pkcs11_lib@"

# Use environment variables for PINs for security
SO_PIN="${SO_PIN:?SO_PIN environment variable not set}"
USER_PIN="${USER_PIN:?USER_PIN environment variable not set}"

echo "Checking TPM token status..."
echo "Using module at: ${MODULE_PATH}"

# Check if the token is already initialized.
if pkcs11-tool --module "${MODULE_PATH}" --list-slots | grep -q 'token initialized'; then
  echo "✅ TPM token is already initialized."
  exit 0
fi

echo "⚠️ TPM token not initialized. Initializing now..."

# 1. Create the token
pkcs11-tool --module "${MODULE_PATH}" \
  --init-token --so-pin="${SO_PIN}" --label="k8s-openbao-token"

# 2. Create the user PIN
pkcs11-tool --module "${MODULE_PATH}" \
  --init-pin --so-pin="${SO_PIN}" --pin="${USER_PIN}"

echo "✅ Initialization complete."
