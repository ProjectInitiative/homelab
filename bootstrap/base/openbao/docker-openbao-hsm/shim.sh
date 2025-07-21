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
    # This makes the absolute path call succeed by redirecting it to our script.
    echo "INFO: [shim.sh] Creating symlink from $EXPECTED_PATH -> $REAL_ENTRYPOINT_PATH"
    mkdir -p /usr/local/bin
    ln -s "$REAL_ENTRYPOINT_PATH" "$EXPECTED_PATH"

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
