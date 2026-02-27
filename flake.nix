{
  description = "A flake for a CDK8s Python development environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    ops-utils.url = "github:projectinitiative/ops-utils";
  };

  outputs = { self, nixpkgs, pyproject-nix, ops-utils, ... }@inputs:
    let
      supportedSystems = [ "x86_64-linux" "aarch64-linux" ];
      forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
      
      # Import the overlay
      overlays = [
        (import ./overlays/default.nix)
      ];

      # Native package sets
      pkgsForSystem = system: import nixpkgs { inherit system; inherit overlays; };

      # Dedicated Cross-Compilation set: Builds ARM on x86_64
      # This is the "secret sauce" to avoid QEMU in CI
      pkgsCrossARM = import nixpkgs {
        system = "x86_64-linux";
        crossSystem = { config = "aarch64-unknown-linux-gnu"; };
        inherit overlays;
      };

      #####################################################################
      # Shared pythonEnv constructor
      #####################################################################
      
      # Helper function to build a python env for a given pkgs set
      mkPythonEnv = pkgs:
        let
          python = pkgs.python3;
          pyproject = pyproject-nix.lib.project.loadPyproject {
            projectRoot = ./pulumi;
          };
          arg = pyproject.renderers.withPackages { inherit python; };
        in python.withPackages arg;

      # Native python environments for each system
      pythonEnvs = forAllSystems (system: mkPythonEnv (pkgsForSystem system));

      # A specific cross-compiled python environment (ARM code, built on x86)
      pythonEnvArmCross = mkPythonEnv pkgsCrossARM;

    in
    {
      packages = forAllSystems (system:
        let
          pkgs = pkgsForSystem system;
          ops = ops-utils.lib.mkUtils { inherit pkgs; };
        in
        {
          # 1. The Native Plugin (Built for current system)
          pulumi-cmp-plugin = import ./pulumi/cmp-image/image.nix { 
            inherit pkgs;
            pythonEnv = pythonEnvs.${system};
          };

          # 2. The Cross-Compiled Plugin (Bypasses QEMU on x86_64)
          # On aarch64-linux, this just points to the native version.
          # On x86_64-linux, this builds aarch64 binaries using cross-compilers.
          pulumi-cmp-plugin-arm-cross = if system == "x86_64-linux" 
            then import ./pulumi/cmp-image/image.nix { 
              pkgs = pkgsCrossARM; 
              pythonEnv = pythonEnvArmCross; 
            }
            else self.packages."aarch64-linux".pulumi-cmp-plugin;

          # Existing scripts and packages
          import-crds = import ./nix/scripts/import-crds.nix { inherit pkgs; };

          generate-manifests = import ./nix/scripts/generate-manifests.nix {  
            inherit pkgs system; 
            pythonEnv = pythonEnvs.${system};
          };

          setup-pulumi = import ./nix/scripts/setup-pulumi.nix { inherit pkgs; };
          diff-manifests = import ./nix/scripts/diff-manifests.nix { inherit pkgs; };
          nixos-remote-builder = import ./nix/images/builder.nix { inherit pkgs; };
          korb = pkgs.callPackage ./nix/pkgs/korb.nix { inherit (pkgs) fetchFromGitHub; };
          
        } // ops);

      apps = forAllSystems (system: 
        let
          pkgs = pkgsForSystem system;
          ops = ops-utils.lib.mkUtils { inherit pkgs; };
          opsApps = ops-utils.lib.mkApps { inherit pkgs; } ops;
        in
        {
          import-crds = {
            type = "app";
            program = "${self.packages.${system}.import-crds}/bin/import-crds";
          };

          generate-manifests = {
            type = "app";
            program = "${self.packages.${system}.generate-manifests}/bin/generate-manifests";
          };

          setup-pulumi = {
            type = "app";
            program = "${self.packages.${system}.setup-pulumi}/bin/setup-pulumi";
          };
          
          diff-manifests = {
            type = "app";
            program = "${self.packages.${system}.diff-manifests}/bin/diff-manifests";
          };
        } // opsApps);

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
              self.packages.${system}.generate-manifests
              self.packages.${system}.setup-pulumi

              self.packages.${system}.build-image
              self.packages.${system}.push-multi-arch
              self.packages.${system}.push-insecure
              self.packages.${system}.dev-push
            ];
            
            shellHook = ''
              export PULUMI_MANIFEST_OUTPUT_DIR=$(pwd)/.direnv/manifests
              echo "Entering Pulumi development shell"
            '';
            
            PULUMI_CONFIG_PASSPHRASE = "";
          };
        }
      );
    };
}