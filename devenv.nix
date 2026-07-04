{ pkgs, config, lib, ... }:

let
  generatorEnv = config.languages.python.import ./generator { };

  # Same scripts as nix run .#* — imported, not duplicated
  generate-manifests = import ./nix/scripts/generate-manifests.nix {
    inherit pkgs;
    pythonEnv = generatorEnv;
  };
  diff-manifests = import ./nix/scripts/diff-manifests.nix {
    inherit pkgs;
    pythonEnv = generatorEnv;
  };
in
{
  cachix.enable = false;

  languages.python = {
    enable = true;
    uv.enable = true;
  };

  packages = [
    pkgs.nodejs_22
    pkgs.cdk8s-cli
    pkgs.dyff
    generatorEnv
    generate-manifests
    diff-manifests
  ];

  scripts.import-crds.exec = ''
    cd generator
    ${pkgs.cdk8s-cli}/bin/cdk8s import
  '';

  enterShell = ''
    echo "╔═══════════════════════════════════════════════╗"
    echo "║     Homelab cdk8s Development Shell           ║"
    echo "╚═══════════════════════════════════════════════╝"
    echo ""
    echo "Available commands:"
    echo "  generate-manifests  - Generate Argo CD Application manifests"
    echo "  diff-manifests      - Diff generated manifests against main"
    echo "  import-crds         - Import CRDs for cdk8s"
    echo ""
  '';

  enterTest = ''
    ${generatorEnv}/bin/python -c "from cdk8s import App; print('cdk8s OK')"
    ${generatorEnv}/bin/python -c "import yaml; print('pyyaml OK')"
  '';
}
