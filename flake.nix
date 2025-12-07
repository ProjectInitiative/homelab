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
          projectRoot = ./pulumi;
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
        # Instantiate all tools
        ops = ops-utils.lib.mkUtils {
          inherit pkgs;
          # supportedSystems defaults to [ "x86_64-linux" "aarch64-linux" ] if omitted
        };

      in
      {
        pulumi-cmp-plugin = import ./pulumi/cmp-image/image.nix { 
          inherit pkgs;
          pythonEnv = pythonEnvs.${system};
        };

        import-crds = import ./nix/scripts/import-crds.nix { inherit pkgs; };

        generate-manifests = import ./nix/scripts/generate-manifests.nix { 
          inherit pkgs system; 
          pythonEnv = pythonEnvs.${system};
        };

        setup-pulumi = import ./nix/scripts/setup-pulumi.nix { inherit pkgs; };

        diff-manifests = import ./nix/scripts/diff-manifests.nix { inherit pkgs; };
      } // ops);

    apps = forAllSystems (system: 
      let
        pkgs = pkgsForSystem system;
        ops = ops-utils.lib.mkUtils { inherit pkgs; };
        
        # Generate apps for all ops tools automatically
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
            self.packages.${system}.diff-manifests
          ];
          
          shellHook = ''
            export PULUMI_MANIFEST_OUTPUT_DIR=$(pwd)/.direnv/manifests
            echo "Entering Pulumi development shell"
            echo "Run 'direnv allow' to automatically load the environment."
            echo "Run 'pulumi new kubernetes-python' to start a new project."
            echo "Run 'import-crds <crd-url>' to generate Python classes for CRDs."
            echo "Run 'generate-manifests' to generate the pulumi k8s manifests."
          '';
          
          PULUMI_CONFIG_PASSPHRASE = "";
        };
      }
    );
  };
}