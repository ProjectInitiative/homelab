#!/bin/bash
# This script, at /bin/sh, intercepts the Helm chart's command.
# It creates a symlink at the absolute path the chart expects,
# pointing it to our real entrypoint. It then executes the original command.

set -e

# This is the exact invocation from the Helm chart.
if [ "$1" = "-ec" ]; then
    FLAGS="$1"
    COMMAND_STRING="$2"

    echo "INFO: [shim.sh] Intercepted Helm chart command."

    # Define the absolute path the script will call.
    EXPECTED_PATH="/usr/local/bin/docker-entrypoint.sh"
    
    # Find the location of our actual, secure entrypoint script.
    REAL_ENTRYPOINT_PATH=$(command -v entrypoint.sh)
    if [ -z "$REAL_ENTRYPOINT_PATH" ]; then
        echo "FATAL: [shim.sh] Could not find 'entrypoint.sh' on the PATH."
        exit 1
    fi

    # Create the necessary directory and the symbolic link.
    # mkdir -p is already idempotent (it does nothing if the dir exists).
    mkdir -p /usr/local/bin

    mkdir -p /tmp
    
    # -s for symbolic, -f for force (overwrite if exists).
    echo "INFO: [shim.sh] Creating/updating symlink from $EXPECTED_PATH -> $REAL_ENTRYPOINT_PATH"
    ln -sf "$REAL_ENTRYPOINT_PATH" "$EXPECTED_PATH"

    # Execute the original, unmodified command string.
    echo "INFO: [shim.sh] Setup complete. Executing original command string..."
    exec bash "$FLAGS" "$COMMAND_STRING"
fi

# Fallback for other commands like liveness probes or interactive shells.
echo "INFO: [shim.sh] Intercepting direct command: $@"
case "$1" in
    "bao" | "openbao")
        exec entrypoint.sh "$@"
        ;;
    "sleep")
        exec "$@"
        ;;
    "")
        echo "INFO: [shim.sh] Starting interactive bash shell."
        exec bash
        ;;
    *)
        echo "FATAL: [shim.sh] Received unknown direct command: '$1'"
        exit 1
        ;;
esac
