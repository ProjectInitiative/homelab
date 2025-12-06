{ pkgs }:
pkgs.writeShellScriptBin "setup-pulumi" ''
  set -e
  echo "Setting up Pulumi..."
  cd pulumi
  ${pkgs.pulumi}/bin/pulumi login --local
  # Create stack if not exists (ignoring error if it exists)
  ${pkgs.pulumi}/bin/pulumi stack select dev --create || true
  # Ensure kubernetes plugin is installed
  ${pkgs.pulumi}/bin/pulumi plugin install resource kubernetes
  echo "✅ Pulumi setup complete."
''