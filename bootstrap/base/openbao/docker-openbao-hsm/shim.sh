#!/bin/bash
# This script, placed at /bin/sh, intercepts Helm chart commands
# and delegates them to the secure entrypoint.sh script.

set -e

# The PATH will be configured in the Dockerfile to find this
SECURE_ENTRYPOINT="entrypoint.sh"

COMMAND_STRING="$2"

case "$COMMAND_STRING" in
  "openbao server"*)
    exec "$SECURE_ENTRYPOINT" server
    ;;
  "bao status"*)
    exec "$SECURE_ENTRYPOINT" status -tls-skip-verify
    ;;
  "sleep "*)
    eval exec "$COMMAND_STRING"
    ;;
  *)
    echo "FATAL: shim.sh received an unknown command: $COMMAND_STRING"
    exit 1
    ;;
esac
