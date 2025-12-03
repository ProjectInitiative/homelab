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
        pkgs = pkgsForSystem system; # Use the new pkgs variable
        import-crds-script = self + "/cdk8s/import-crds.py";
      in
      {
        import-crds = pkgs.writeShellScriptBin "import-crds" ''
          #!${pkgs.stdenv.shell}
          export TMPDIR=/tmp
          export PATH=${pkgs.lib.makeBinPath [ pkgs.python3 pkgs.cdk8s-cli pkgs.nodejs ]}:$PATH
          ${import-crds-script} "$@"
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
            pkgs = pkgsForSystem system; # Use the new pkgs variable
            python = pkgs.python3;
        pyproject = pyproject-nix.lib.project.loadPyproject {
          projectRoot = self;
        };

        pythonEnv = python.withPackages (pyproject.renderers.withPackages { inherit python; });

      in {
        default = pkgs.mkShell {
          packages = [
            pythonEnv
            pkgs.cdk8s-cli
            pkgs.direnv
            pkgs.nix-direnv
            pkgs.uv
            pkgs.nodejs
            self.packages.${system}.import-crds
          ];
          
          shellHook = ''
            echo "Entering CDK8s development shell"
            echo "Run 'direnv allow' to automatically load the environment."
            echo "Then run 'cdk8s init python-app' to start your project."
            echo "To import CRDs, run 'import-crds'."
          '';
        };
      }
    );
  };
}
