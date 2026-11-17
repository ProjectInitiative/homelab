#!/bin/sh
set -eu

if [ "$#" -eq 0 ]; then
  echo 'usage: flare-ignition-prep export <recipe-or-checkpoint> [ignition options...]' >&2
  exit 64
fi

# Keep the source tree and toolchain immutable. Callers provide the output,
# cache, rendezvous, and signing/trust paths explicitly through Ignition flags
# and mounted workspace paths.
exec /opt/flare/.venv/bin/ignition "$@"
