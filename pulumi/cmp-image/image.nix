{ pkgs, pythonEnv }:

let
  pulumiInit = pkgs.writeShellScriptBin "pulumi-init" ''
    export HOME=/home/argocd
    export PATH=${pythonEnv}/bin:$PATH
    ${pkgs.pulumi}/bin/pulumi login --local
    ${pkgs.pulumi}/bin/pulumi stack select dev --create || true
  '';

  pulumiGenerate = pkgs.writeShellScriptBin "pulumi-generate" ''
    export HOME=/home/argocd
    export PATH=${pythonEnv}/bin:$PATH
    ${pkgs.pulumi}/bin/pulumi up --yes --skip-preview 1>&2
    ${pkgs.gawk}/bin/awk 'FNR==1 && NR!=1 {print "---"} {print}' /tmp/manifests/1-manifest/*.yaml
  '';

# Switch back to buildLayeredImage to unlock fakeRootCommands
in pkgs.dockerTools.buildLayeredImage {
  name = "pulumi-cmp-plugin";
  tag = "latest";

  config = {
    Env = [ 
      "PATH=/bin" 
      "HOME=/home/argocd" 
      "PULUMI_CONFIG_PASSPHRASE=" 
    ];
    User = "999";
    WorkingDir = "/app/pulumi";
  };

  # buildLayeredImage uses 'contents' instead of 'copyToRoot' + 'buildEnv'
  contents = [
    pkgs.cacert
    pkgs.pulumiPackages.pulumi-python
    pkgs.bash
    pkgs.coreutils
    pkgs.fakeNss
    pulumiInit
    pulumiGenerate
  ];

  # Executes in a pure user-space fakeroot environment.
  # No QEMU VM is booted, bypassing the virtiofsd CI bug.
  fakeRootCommands = ''
    mkdir -p ./home/argocd/.pulumi
    mkdir -p ./tmp
    chmod 1777 ./tmp
    chown -R 999:999 ./home/argocd
  '';
}