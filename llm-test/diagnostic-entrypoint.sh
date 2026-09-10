#!/bin/sh
set -eu
python3 /tmp/patch-skip-init-memory-check.py
exec "$@"
