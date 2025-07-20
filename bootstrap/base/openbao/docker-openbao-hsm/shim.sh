#!/bin/bash
# This script, at /bin/sh, is a smart shim for Helm chart compatibility.
# It intercepts the startup command, hijacks calls to 'bao' and others to
# redirect them to a secure entrypoint, and then executes the original
# command using a real shell.

set -e

# ---
# CASE 1: Handle the specific Helm Chart invocation.
# Helm calls this script as: /bin/sh -ec "long command string..."
# So, $1 will be "-ec" and $2 will be the command string.
# ---
if [ "$1" = "-ec" ]; then
    FLAGS="$1"
    COMMAND_STRING="$2"

    if [ -z "$COMMAND_STRING" ]; then
        echo "FATAL: [shim.sh] Received flags '$FLAGS' but no command string."
        exit 1
    fi

    echo "INFO: [shim.sh] Intercepting Helm chart command."

    # Find the absolute path of our secure entrypoint.
    SECURE_ENTRYPOINT_PATH=$(command -v entrypoint.sh)
    if [ -z "$SECURE_ENTRYPOINT_PATH" ]; then
        echo "FATAL: [shim.sh] Could not find 'entrypoint.sh' in PATH."
        exit 1
    fi

    # Create a temporary directory for our hijack executables.
    # mktemp is provided by the 'coreutils' dependency in shim.nix.
    mkdir -p /tmp
    HIJACK_DIR=$(mktemp -d)
    trap 'rm -rf "$HIJACK_DIR"' EXIT # Clean up on exit

    # Create symlinks that hijack calls and redirect them to our secure script.
    # These are the commands the Helm script tries to run.
    ln -s "$SECURE_ENTRYPOINT_PATH" "$HIJACK_DIR/bao"
    ln -s "$SECURE_ENTRYPOINT_PATH" "$HIJACK_DIR/openbao"
    ln -s "$SECURE_ENTRYPOINT_PATH" "$HIJACK_DIR/docker-entrypoint.sh"

    # Prepend our hijack directory to the PATH.
    # Now, any call to 'bao' etc., inside the COMMAND_STRING will resolve here first.
    export PATH="$HIJACK_DIR:$PATH"

    echo "INFO: [shim.sh] Hijacking calls via PATH: $PATH"
    echo "INFO: [shim.sh] Executing original script with real 'bash' interpreter..."

    # Execute the original command string using a real shell ('bash' from our
    # Nix dependencies), passing along the original flags (-ec). This is much
    # safer and more robust than 'eval'.
    exec bash "$FLAGS" "$COMMAND_STRING"
fi

# ---
# CASE 2: Handle all other invocations (e.g., liveness probes, interactive shells).
# ---
echo "INFO: [shim.sh] Intercepting direct command: $@"

# For simple commands like 'bao status', this will delegate directly.
# For an interactive shell ('docker exec -it <pod> /bin/sh'), this will
# provide a real bash shell.
case "$1" in
    "bao" | "openbao")
        # Delegate directly to the secure entrypoint
        exec entrypoint.sh "$@"
        ;;
    "sleep")
        # Allow sleep commands for probes
        exec "$@"
        ;;
    "")
        # No command, user wants an interactive shell
        echo "INFO: [shim.sh] No command specified. Starting interactive bash shell."
        exec bash
        ;;
    *)
        echo "FATAL: [shim.sh] Received unknown direct command: '$1'"
        exit 1
        ;;
esac
