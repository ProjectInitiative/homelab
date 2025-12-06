{ pkgs, supportedSystems }:
pkgs.writeShellScriptBin "push-multi-arch" ''
  set -e
  set -o pipefail

  PACKAGE_NAME=$1
  IMAGE_NAME=$2
  OWNER=$3
  TAG=''${4:-latest}

  if [ -z "$PACKAGE_NAME" ] || [ -z "$IMAGE_NAME" ] || [ -z "$OWNER" ]; then
    echo "Usage: $0 <package-name> <image-name> <owner> [tag]"
    exit 1
  fi

  # Define systems to build for
  SYSTEMS=(${builtins.toString supportedSystems})
  MANIFEST_LIST=()

  for ARCH_SYSTEM in "''${SYSTEMS[@]}"; do
    # Derive arch from system string
    ARCH=$(echo "$ARCH_SYSTEM" | sed 's/-linux//' | sed 's/x86_64/amd64/' | sed 's/aarch64/arm64/')
    
    echo "--- Building for $ARCH_SYSTEM ($ARCH) ---"
    nix build ".#packages.$ARCH_SYSTEM.$PACKAGE_NAME" -o "result-$PACKAGE_NAME-$ARCH"
    
    LOADED_IMAGE=$(docker load < "result-$PACKAGE_NAME-$ARCH" | grep "Loaded image" | sed 's/Loaded image: //')
    echo "Loaded image: $LOADED_IMAGE"

    TARGET_TAG="ghcr.io/$OWNER/$IMAGE_NAME:$TAG-$ARCH"
    echo "Tagging $LOADED_IMAGE as $TARGET_TAG"
    docker tag "$LOADED_IMAGE" "$TARGET_TAG"
    
    echo "Pushing $TARGET_TAG"
    docker push "$TARGET_TAG"

    MANIFEST_LIST+=("$TARGET_TAG")
    
    rm "result-$PACKAGE_NAME-$ARCH"
  done

  MANIFEST_TAG="ghcr.io/$OWNER/$IMAGE_NAME:$TAG"
  echo "--- Creating and pushing manifest for $MANIFEST_TAG ---"
  docker manifest create "$MANIFEST_TAG" "''${MANIFEST_LIST[@]}"
  docker manifest push "$MANIFEST_TAG"

  echo "✅ Successfully pushed multi-arch image $MANIFEST_TAG"
''