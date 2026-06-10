{
  description = "Homelab — Pulumi manifest generator for Argo CD";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";
    flake-parts.inputs.nixpkgs-lib.follows = "nixpkgs";
    devenv.url = "github:cachix/devenv";
    devenv.inputs.nixpkgs.follows = "nixpkgs";
    nix2container.url = "github:nlewo/nix2container";
    nix2container.inputs.nixpkgs.follows = "nixpkgs";
    mk-shell-bin.url = "github:rrbutani/nix-mk-shell-bin";
    ops-utils.url = "github:projectinitiative/ops-utils";
  };

  nixConfig = {
    extra-trusted-public-keys = "devenv.cachix.org-1:w1cLUi8dv3hnoSPGAuibQv+f9TZLr6cv/Hm9XgU50cw=";
    extra-substituters = "https://devenv.cachix.org";
  };

  outputs =
    inputs@{ flake-parts, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      imports = [
        inputs.devenv.flakeModule
      ];

      systems = [
        "x86_64-linux"
        "aarch64-linux"
      ];

      perSystem =
        { config, pkgs, lib, system, ... }:
        let
          # -------------------------------------------------------------------
          # Python environment
          # -------------------------------------------------------------------
          pulumiCrds = pkgs.python3.pkgs.buildPythonPackage rec {
            pname = "pulumi-crds";
            version = "4.23.0";
            src = ./pulumi/crds;
            format = "pyproject";
            nativeBuildInputs = with pkgs.python3.pkgs; [ setuptools ];
            propagatedBuildInputs = [
              pkgs.python3.pkgs.pulumi
              pkgs.python3.pkgs."pulumi-kubernetes"
              pkgs.python3.pkgs.parver
              pkgs.python3.pkgs.semver
              pkgs.python3.pkgs.requests
              pkgs.python3.pkgs."typing-extensions"
            ];
            doCheck = false;
          };

          pythonEnv = pkgs.python3.withPackages (_: [
            (pkgs.python3.pkgs.pulumi)
            (pkgs.python3.pkgs."pulumi-kubernetes")
            (pkgs.python3.pkgs.parver)
            (pkgs.python3.pkgs.semver)
            (pkgs.python3.pkgs.pyyaml)
            (pkgs.python3.pkgs.requests)
            (pkgs.python3.pkgs."typing-extensions")
            (pkgs.python3.pkgs.pip)
            pulumiCrds
          ]);

          # -------------------------------------------------------------------
          # Cross-compiled Python env (ARM on x86_64 for CMP image)
          # -------------------------------------------------------------------
          pkgsCrossARM = import inputs.nixpkgs {
            system = "x86_64-linux";
            crossSystem = { config = "aarch64-unknown-linux-gnu"; };
          };

          pulumiCrdsArm = pkgsCrossARM.python3.pkgs.buildPythonPackage rec {
            pname = "pulumi-crds";
            version = "4.23.0";
            src = ./pulumi/crds;
            format = "pyproject";
            nativeBuildInputs = with pkgsCrossARM.python3.pkgs; [ setuptools ];
            propagatedBuildInputs = [
              pkgsCrossARM.python3.pkgs.pulumi
              pkgsCrossARM.python3.pkgs."pulumi-kubernetes"
              pkgsCrossARM.python3.pkgs.parver
              pkgsCrossARM.python3.pkgs.semver
              pkgsCrossARM.python3.pkgs.requests
              pkgsCrossARM.python3.pkgs."typing-extensions"
            ];
            doCheck = false;
          };

          pythonEnvArm = pkgsCrossARM.python3.withPackages (ps: [
            ps.pulumi
            ps."pulumi-kubernetes"
            ps.parver
            ps.semver
            ps.pyyaml
            ps.requests
            ps."typing-extensions"
            pulumiCrdsArm
          ]);

          # -------------------------------------------------------------------
          # Shared ops-utils helpers
          # -------------------------------------------------------------------
          ops = inputs.ops-utils.lib.mkUtils { inherit pkgs; };

        in
        {
          # -------------------------------------------------------------------
          # Packages
          # -------------------------------------------------------------------
          packages = {

            # --- CMP Plugin Containers ---
            pulumi-cmp-plugin = import ./pulumi/cmp-image/image.nix {
              inherit pkgs;
              inherit pythonEnv;
            };

            pulumi-cmp-plugin-arm-cross =
              if system == "x86_64-linux"
              then import ./pulumi/cmp-image/image.nix {
                pkgs = pkgsCrossARM;
                pythonEnv = pythonEnvArm;
              }
              else config.packages.pulumi-cmp-plugin;

            # --- Utility Scripts ---
            import-crds = import ./nix/scripts/import-crds.nix { inherit pkgs; };

            generate-manifests = import ./nix/scripts/generate-manifests.nix {
              inherit pkgs system;
              inherit pythonEnv;
            };

            setup-pulumi = import ./nix/scripts/setup-pulumi.nix { inherit pkgs; };

            diff-manifests = import ./nix/scripts/diff-manifests.nix { inherit pkgs; };

            # --- System Images ---
            nixos-remote-builder = import ./nix/images/builder.nix { inherit pkgs; };

            # --- Go Tools ---
            korb = pkgs.callPackage ./nix/pkgs/korb.nix {
              inherit (pkgs) fetchFromGitHub;
            };

          } // ops;

          # -------------------------------------------------------------------
          # Development Shell (devenv)
          # -------------------------------------------------------------------
          devenv.shells.default = {
            imports = [ ./devenv.nix ];
            packages = [ pythonEnv ];
            # devenv.root must be set explicitly for use devenv + flake-parts
            # to avoid read-only filesystem issues
            devenv.root = lib.mkForce (toString ./.);
          };

          # -------------------------------------------------------------------
          # Apps
          # -------------------------------------------------------------------
          apps = {
            import-crds = {
              type = "app";
              program = "${config.packages.import-crds}/bin/import-crds";
            };

            generate-manifests = {
              type = "app";
              program = "${config.packages.generate-manifests}/bin/generate-manifests";
            };

            setup-pulumi = {
              type = "app";
              program = "${config.packages.setup-pulumi}/bin/setup-pulumi";
            };

            diff-manifests = {
              type = "app";
              program = "${config.packages.diff-manifests}/bin/diff-manifests";
            };
          } // builtins.mapAttrs (name: value: value) (inputs.ops-utils.lib.mkApps { inherit pkgs; } ops);

          # -------------------------------------------------------------------
          # Checks
          # -------------------------------------------------------------------
          checks.formatting =
            pkgs.runCommand "check-formatting"
              {
                nativeBuildInputs = [ pkgs.nixfmt ];
                src = ./.;
              }
              ''
                nixfmt --check $src/*.nix $src/devenv.nix
                touch $out
              '';

          formatter = pkgs.nixfmt;
        };

      flake = { };
    };
}
