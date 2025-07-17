#!/bin/sh
set -e

MODULE_PATH="@tpm_pkcs11_lib@"
SO_PIN="${SO_PIN:?SO_PIN environment variable not set}"
USER_PIN="${USER_PIN:?USER_PIN environment variable not set}"
TOKEN_NAME="${TOKEN_NAME:?TOKEN_NAME environment variable not set}"

echo "Checking TPM token status..."
if pkcs11-tool --module "${MODULE_PATH}" --list-slots | grep -q 'token initialized'; then
  echo "✅ TPM token is already initialized."
else
  echo "⚠️ TPM token not initialized. Initializing now..."
  pkcs11-tool --module "${MODULE_PATH}" --init-token --so-pin="${SO_PIN}" --label="${TOKEN_NAME}"
  pkcs11-tool --module "${MODULE_PATH}" --init-pin --so-pin="${SO_PIN}" --pin="${USER_PIN}"
  echo "✅ Initialization complete."
fi

# echo "Searching for FAPI profiles in /nix/store..."
# PROFILE_SRC_DIR=$(find /nix/store -name "fapi-profiles" -type d | head -n 1)

# if [ -z "$PROFILE_SRC_DIR" ]; then
#   echo "❌ FAPI profiles directory not found. This is unexpected."
#   exit 1
# fi

# echo "Found FAPI profiles at: $PROFILE_SRC_DIR"
# TARGET_DIR="/var/lib/openbao-tpm/fapi-profiles/"
# echo "Copying profiles to shared volume at $TARGET_DIR..."
# mkdir -p "$TARGET_DIR"
# cp -rT "$PROFILE_SRC_DIR" "$TARGET_DIR"
# echo "✅ Profiles copied successfully."

# echo "Changing ownership of shared volume to user 1000..."
# chown -R 1000:1000 /var/lib/openbao-tpm
# echo "✅ Ownership changed."

# # Add read and execute permissions for all users.
# echo "Setting read/execute permissions on shared volume..."
# chmod -R a+rX /var/lib/openbao-tpm
# echo "✅ Permissions set."

exit 0
