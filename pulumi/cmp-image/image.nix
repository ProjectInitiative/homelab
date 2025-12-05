{ pkgs, pythonEnv }:

let
  pulumiInit = pkgs.writeShellScriptBin "pulumi-init" ''
    export HOME=/home/argocd
    pulumi login --local
    # Create stack if not exists (ignoring error if it exists)
    pulumi stack select dev --create || true
    # Ensure kubernetes plugin is installed
    pulumi plugin install resource kubernetes
  '';

  pulumiGenerate = pkgs.writeShellScriptBin "pulumi-generate" ''
    export HOME=/home/argocd
    export PYTHONPATH=$PYTHONPATH:$(pwd)/crds
    # Run pulumi up, redirecting output to stderr so it doesn't pollute the manifest stream
    pulumi up --yes --skip-preview 1>&2
    # Concatenate all generated YAML files to stdout
    awk 'FNR==1 && NR!=1 {print "---"} {print}' ./manifests/1-manifest/*.yaml
  '';
in pkgs.dockerTools.buildImage {
  name = "pulumi-cmp-plugin";
  tag = "latest";
  
  config = {
    # Set environment variables
    Env = [
      "PATH=${pkgs.lib.makeBinPath [
        pythonEnv
        pkgs.pulumi
        pkgs.bash
        pkgs.coreutils
        pkgs.findutils
        pkgs.gawk
        pkgs.git
        pkgs.grep
        pkgs.sed
      ]}:${pulumiInit}/bin:${pulumiGenerate}/bin"
      "HOME=/home/argocd"
      "PULUMI_HOME=/home/argocd/.pulumi"
    ];
    
    # Argo CD typically uses user 999
    User = "999";
    
    # Working directory (will be overridden by Argo CD, but good default)
    WorkingDir = "/home/argocd";
  };
  
  copyToRoot = pkgs.buildEnv {
    name = "image-root";
    paths = [
      pythonEnv
      pkgs.pulumi
      pkgs.bash
      pkgs.coreutils
      pkgs.findutils
      pkgs.gawk
      pkgs.git
      pkgs.grep
      pkgs.sed
      pkgs.fakeNss
      pulumiInit
      pulumiGenerate
    ];
    pathsToLink = [ "/bin" "/etc" "/var" "/tmp" ];
  };
  
  # Create necessary directories with correct permissions
  runAsRoot = ''
    mkdir -p /home/argocd/.pulumi
    mkdir -p /tmp
    chmod 1777 /tmp
    chown -R 999:999 /home/argocd
  '';
}
