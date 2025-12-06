{ pkgs }:
pkgs.writeShellScriptBin "dev-push" ''
  set -e
  INSECURE_REGISTRY=$1
  if [ -z "$INSECURE_REGISTRY" ]; then
    echo "Usage: $0 <insecure-registry>"
    exit 1
  fi
  nix run .#push-insecure -- pulumi-cmp-plugin pulumi-cmp-plugin $INSECURE_REGISTRY
''