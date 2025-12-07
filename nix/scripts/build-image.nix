{ pkgs, system }:
pkgs.writeShellScriptBin "build-image" ''
  set -e
  echo "Building Pulumi CMP image for ${system}..."
  nix build ".#packages.${system}.pulumi-cmp-plugin" -o result-image
  echo "Loading into Docker..."
  docker load < result-image
  rm result-image
  echo "✅ Pulumi CMP image for ${system} ready!"
''