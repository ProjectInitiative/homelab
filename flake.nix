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
  in
  {
    packages = forAllSystems (system:
      let
        pkgs = pkgsForSystem system;
      in
      {
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
      });

    apps = forAllSystems (system: {
      import-crds = {
        type = "app";
        program = "${self.packages.${system}.import-crds}/bin/import-crds";
      };
    });

    devShells = forAllSystems (system:
      let
        pkgs = pkgsForSystem system;
        python = pkgs.python3;
        pyproject = pyproject-nix.lib.project.loadPyproject {
          projectRoot = self;
        };

        pythonEnv = python.withPackages (pyproject.renderers.withPackages { inherit python; });

      in {
        default = pkgs.mkShell {
          packages = [
            pythonEnv
            pkgs.pulumi
            pkgs.crd2pulumi
            pkgs.pulumiPackages.pulumi-python
            pkgs.direnv
            pkgs.nix-direnv
            pkgs.uv
            self.packages.${system}.import-crds
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
