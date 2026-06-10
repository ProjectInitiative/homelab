{ pkgs, config, ... }:
{
  cachix.enable = false;

  languages.python = {
    enable = true;
    uv.enable = true;
    uv.sync.enable = false;
  };

  packages = with pkgs; [
    pulumi
    pulumiPackages.pulumi-python
    crd2pulumi
    python3Packages.deepdiff
    direnv
    nix-direnv
  ];

  env = {
    PULUMI_CONFIG_PASSPHRASE = "";
    PULUMI_ACCESS_TOKEN = "";
    PULUMI_MANIFEST_OUTPUT_DIR = "$PWD/.direnv/manifests";
  };

  scripts = {
    generate-manifests.exec = ''
      mkdir -p "$PULUMI_MANIFEST_OUTPUT_DIR"
      cd pulumi
      pulumi up --yes --skip-preview
    '';

    import-crds.exec = ''
      crd2pulumi --pythonPath ./pulumi/crds \
        $(python3 -c "import json; print(' '.join(json.load(open('pulumi/crd-imports.json'))))") \
        --force
    '';

    setup-pulumi.exec = ''
      cd pulumi
      pulumi login --local
      pulumi stack select dev --create || true
      pulumi plugin install resource kubernetes
    '';
  };

  enterShell = ''
    # Sync Python deps from uv.lock (project is in pulumi/)
    uv sync --project pulumi 2>/dev/null || true

    echo "╔═══════════════════════════════════════════════╗"
    echo "║     Homelab Pulumi Development Shell         ║"
    echo "╚═══════════════════════════════════════════════╝"
    echo ""
    echo "Available commands:"
    echo "  generate-manifests  - Generate Argo CD Application manifests"
    echo "  import-crds         - Import CRDs for Pulumi"
    echo "  setup-pulumi        - Setup Pulumi configuration"
    echo "  diff-manifests      - Diff generated manifests against current state"
    echo ""
    echo "Python: $(python3 --version)"
    echo "Pulumi: $(pulumi version)"
  '';

  enterTest = ''
    cd pulumi
    python3 -c "from pulumi_crds.argoproj.v1alpha1 import Application; print('pulumi_crds import OK')"
  '';
}
