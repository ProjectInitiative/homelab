{
  description = "A flake for a CDK8s Python development environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, pyproject-nix, ... }@inputs:
  let
    supportedSystems = [ "x86_64-linux" "aarch64-linux" ];
    forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
    
    # Import the overlay
    overlays = [
      (import ./overlays/default.nix)
    ];

    # Define pkgs with overlays applied
    pkgsForSystem = system: import nixpkgs { inherit system; inherit overlays; };

    #####################################################################
    # Shared pythonEnv constructor
    #####################################################################
    pythonEnvs = forAllSystems (system:
      let
        # This is where the magic happens!
        pkgs = pkgsForSystem system;
        # Use the python from our custom pkgs. It now contains the overlaid packages.
        python = pkgs.python3;
        # Loads pyproject.toml into a high-level project representation
        # Do you notice how this is not tied to any `system` attribute or package sets?
        # That is because `project` refers to a pure data representation.
        pyproject = pyproject-nix.lib.project.loadPyproject {
          # Read & unmarshal pyproject.toml relative to this project root.
          # projectRoot is also used to set `src` for renderers such as buildPythonPackage.
          projectRoot = ./.;
        };
        # Returns a function that can be passed to `python.withPackages`
        arg = pyproject.renderers.withPackages { inherit python; };
      # Returns a wrapped environment (virtualenv like) with all our packages
      in python.withPackages arg
    );

  in
  {
    packages = forAllSystems (system:
      let
        pkgs = pkgsForSystem system;
      in
      {
        pulumi-cmp-image = import ./pulumi/cmp-image/image.nix { 
          inherit pkgs;
          pythonEnv = pythonEnvs.${system};
        };

        import-crds = pkgs.writeShellScriptBin "import-crds" ''
          #!${pkgs.stdenv.shell}
          # Usage: import-crds <path-to-json-file>
          # Example: import-crds cdk8s/crd-imports.json
          
          if [ -z "$1" ]; then
            echo "Usage: import-crds <path-to-json-file>"
            exit 1
          fi

          JSON_FILE="$1"
          
          if [ ! -f "$JSON_FILE" ]; then
             echo "Error: File $JSON_FILE not found."
             exit 1
          fi

          echo "Reading CRDs from $JSON_FILE..."
          
          # Extract CRDs from JSON using Python
          CRD_ARGS=$(${pkgs.python3}/bin/python3 -c "import json, sys; print(' '.join(json.load(open('$JSON_FILE'))))")
          
          echo "Running crd2pulumi..."
          # Generate Python types for the CRDs
          # shellcheck disable=SC2086
          ${pkgs.crd2pulumi}/bin/crd2pulumi --pythonOut ./pulumi/crds "$1" --force
        '';

        build-image = pkgs.writeShellScriptBin "build-image" ''
          set -e
          echo "Building Pulumi CMP image for ${system}..."
          nix build ".#packages.${system}.pulumi-cmp-image" -o result-image
          echo "Loading into Docker..."
          docker load < result-image
          rm result-image
          echo "✅ Pulumi CMP image for ${system} ready!"
        '';

        push-multi-arch = pkgs.writeShellScriptBin "push-multi-arch" ''
          set -e
          set -o pipefail

          IMAGE_NAME=$1
          OWNER=$2
          TAG=''${3:-latest}

          if [ -z "$IMAGE_NAME" ] || [ -z "$OWNER" ]; then
            echo "Usage: $0 <image-name> <owner> [tag]"
            exit 1
          fi

          # Define systems to build for
          SYSTEMS=(${builtins.toString supportedSystems})
          MANIFEST_LIST=()

          for ARCH_SYSTEM in "''${SYSTEMS[@]}"; do
            # Derive arch from system string
            ARCH=$(echo "$ARCH_SYSTEM" | sed 's/-linux//' | sed 's/x86_64/amd64/' | sed 's/aarch64/arm64/')
            
            echo "--- Building for $ARCH_SYSTEM ($ARCH) ---"
            nix build ".#packages.$ARCH_SYSTEM.pulumi-cmp-image" -o "result-$ARCH"
            
            LOADED_IMAGE=$(docker load < "result-$ARCH" | grep "Loaded image" | sed 's/Loaded image: //')
            echo "Loaded image: $LOADED_IMAGE"

            TARGET_TAG="ghcr.io/$OWNER/$IMAGE_NAME:$TAG-$ARCH"
            echo "Tagging $LOADED_IMAGE as $TARGET_TAG"
            docker tag "$LOADED_IMAGE" "$TARGET_TAG"
            
            echo "Pushing $TARGET_TAG"
            docker push "$TARGET_TAG"

            MANIFEST_LIST+=("$TARGET_TAG")
            
            rm "result-$ARCH"
          done

          MANIFEST_TAG="ghcr.io/$OWNER/$IMAGE_NAME:$TAG"
          echo "--- Creating and pushing manifest for $MANIFEST_TAG ---"
          docker manifest create "$MANIFEST_TAG" "''${MANIFEST_LIST[@]}"
          docker manifest push "$MANIFEST_TAG"

          echo "✅ Successfully pushed multi-arch image $MANIFEST_TAG"
        '';
      });

    apps = forAllSystems (system: 
      let
        pkgs = pkgsForSystem system;
      in
      {
        import-crds = {
          type = "app";
          program = "${self.packages.${system}.import-crds}/bin/import-crds";
        };

        build-image = {
          type = "app";
          program = "${self.packages.${system}.build-image}/bin/build-image";
        };

        push-multi-arch = {
          type = "app";
          program = "${self.packages.${system}.push-multi-arch}/bin/push-multi-arch";
        };
      });

    devShells = forAllSystems (system:
      let
        pkgs = pkgsForSystem system;
        pythonEnv = pythonEnvs.${system};

      in {
        default = pkgs.mkShell {
          packages = [ pythonEnv ] ++ [
            pkgs.pulumi
            pkgs.crd2pulumi
            pkgs.pulumiPackages.pulumi-python
            pkgs.direnv
            pkgs.nix-direnv
            pkgs.uv
            pkgs.python3Packages.deepdiff
            self.packages.${system}.import-crds
            self.packages.${system}.build-image
            self.packages.${system}.push-multi-arch
          ];
          
          shellHook = ''
            echo "Entering Pulumi development shell"
            echo "Run 'direnv allow' to automatically load the environment."
            echo "Run 'pulumi new kubernetes-python' to start a new project."
            echo "Use 'import-crds <crd-url>' to generate Python classes for CRDs."
          '';
          
          PULUMI_CONFIG_PASSPHRASE = "";
        };
      }
    );
  };
}