{ pkgs, system }:
pkgs.writeShellScriptBin "push-insecure" ''
  set -e
  set -o pipefail

  PACKAGE_NAME=$1
  IMAGE_NAME=$2
  INSECURE_REGISTRY=$3
  TAG=''${4:-latest}

  if [ -z "$PACKAGE_NAME" ] || [ -z "$IMAGE_NAME" ] || [ -z "$INSECURE_REGISTRY" ]; then
    echo "Usage: $0 <package-name> <image-name> <insecure-registry> [tag]"
    exit 1
  fi

  # Assume current system for dev push
  SYSTEM="${system}"
  # Derive arch from system string
  ARCH=$(echo "$SYSTEM" | sed 's/-linux//' | sed 's/x86_64/amd64/' | sed 's/aarch64/arm64/')

  echo "--- Building $PACKAGE_NAME for $SYSTEM ($ARCH) ---"
  nix build ".#packages.$SYSTEM.$PACKAGE_NAME" -o "result-$PACKAGE_NAME-$ARCH"
  
  LOADED_IMAGE=$(docker load < "result-$PACKAGE_NAME-$ARCH" | grep "Loaded image" | sed 's/Loaded image: //')
  echo "Loaded image: $LOADED_IMAGE"

  TARGET_TAG="$INSECURE_REGISTRY/$IMAGE_NAME:$TAG"
  echo "Tagging $LOADED_IMAGE as $TARGET_TAG"
  docker tag "$LOADED_IMAGE" "$TARGET_TAG"
  
  echo "Pushing $TARGET_TAG"
  docker push "$TARGET_TAG"

  rm "result-$PACKAGE_NAME-$ARCH"

  echo "✅ Successfully pushed image $TARGET_TAG"
''