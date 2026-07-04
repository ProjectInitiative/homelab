{
  description = "Homelab — cdk8s manifest generator for Argo CD";

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
    uv2nix.url = "github:pyproject-nix/uv2nix";
    uv2nix.inputs.nixpkgs.follows = "nixpkgs";
    pyproject-nix.url = "github:pyproject-nix/pyproject.nix";
    pyproject-nix.inputs.nixpkgs.follows = "nixpkgs";
    pyproject-build-systems.url = "github:pyproject-nix/build-system-pkgs";
    pyproject-build-systems.inputs.nixpkgs.follows = "nixpkgs";
    pyproject-build-systems.inputs.uv2nix.follows = "uv2nix";
    pyproject-build-systems.inputs.pyproject-nix.follows = "pyproject-nix";
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
          ops = inputs.ops-utils.lib.mkUtils { inherit pkgs; };

          # --- uv2nix: build a hermetic Python virtualenv from generator/uv.lock ---
          # Used by flake packages (generate-manifests, diff-manifests, cmp-image).
          # The devenv shell uses config.languages.python.import (same uv2nix under the hood).
          workspace = inputs.uv2nix.lib.workspace.loadWorkspace {
            workspaceRoot = ./generator;
          };
          overlay = workspace.mkPyprojectOverlay {
            sourcePreference = "wheel";
          };
          python = pkgs.python311;
          pythonBase = pkgs.callPackage inputs.pyproject-nix.build.packages {
            inherit python;
          };
          pythonSet = pythonBase.overrideScope (
            lib.composeManyExtensions [
              inputs.pyproject-build-systems.overlays.default
              overlay
            ]
          );
          pythonEnv = pythonSet.mkVirtualEnv "homelab-generator-env" workspace.deps.default;

          # Cross-compiled env for ARM CMP image
          pkgsCrossARM = import inputs.nixpkgs {
            system = "x86_64-linux";
            crossSystem = { config = "aarch64-unknown-linux-gnu"; };
          };
          pythonCross = pkgsCrossARM.python311;
          pythonBaseCross = pkgsCrossARM.callPackage inputs.pyproject-nix.build.packages {
            python = pythonCross;
          };
          pythonSetCross = pythonBaseCross.overrideScope (
            lib.composeManyExtensions [
              inputs.pyproject-build-systems.overlays.default
              overlay
            ]
          );
          pythonEnvCross = pythonSetCross.mkVirtualEnv "homelab-generator-env-cross" workspace.deps.default;

        in
        {
          packages = {
            cmp-image = import ./generator/cmp-image/image.nix {
              inherit pkgs pythonEnv;
            };

            cmp-image-arm-cross =
              if system == "x86_64-linux"
              then import ./generator/cmp-image/image.nix {
                pkgs = pkgsCrossARM;
                pythonEnv = pythonEnvCross;
              }
              else config.packages.cmp-image;

            import-crds = import ./nix/scripts/import-crds.nix { inherit pkgs; };

            generate-manifests = import ./nix/scripts/generate-manifests.nix {
              inherit pkgs pythonEnv;
            };

            diff-manifests = import ./nix/scripts/diff-manifests.nix {
              inherit pkgs pythonEnv;
            };

            nixos-remote-builder = import ./nix/images/builder.nix { inherit pkgs; };

            korb = pkgs.callPackage ./nix/pkgs/korb.nix {
              inherit (pkgs) fetchFromGitHub;
            };
          } // ops;

          devenv.shells.default = {
            imports = [ ./devenv.nix ];
            devenv.root = toString ./.;
          };

          apps = {
            import-crds = {
              type = "app";
              program = "${config.packages.import-crds}/bin/import-crds";
            };
            generate-manifests = {
              type = "app";
              program = "${config.packages.generate-manifests}/bin/generate-manifests";
            };
            diff-manifests = {
              type = "app";
              program = "${config.packages.diff-manifests}/bin/diff-manifests";
            };
          } // builtins.mapAttrs (name: value: value) (inputs.ops-utils.lib.mkApps { inherit pkgs; } ops);

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
