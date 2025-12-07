{ pkgs, pythonEnv, system }:
pkgs.writeShellScriptBin "generate-manifests" ''
  set -e
  # Add python environment to PATH so Pulumi can find dependencies
  export PATH="${pythonEnv}/bin:$PATH"

  # Navigate to pulumi directory as expected by the project structure
  cd pulumi
  
  # Set output directory to .direnv/manifests in the project root
  # (one level up from pulumi dir) if not already set
  if [ -z "$PULUMI_MANIFEST_OUTPUT_DIR" ]; then
    export PULUMI_MANIFEST_OUTPUT_DIR=$(pwd)/../.direnv/manifests
  fi
  mkdir -p "$PULUMI_MANIFEST_OUTPUT_DIR"
  
  echo "Generating manifests to $PULUMI_MANIFEST_OUTPUT_DIR..."
  ${pkgs.pulumi}/bin/pulumi up --yes --skip-preview
  echo "✅ Manifests generated in $PULUMI_MANIFEST_OUTPUT_DIR"
''