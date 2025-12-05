{ pkgs, pythonEnv }:

let
  # We reference the store paths directly in the scripts.
  # Note: Pulumi needs 'python3' in the PATH to launch the language host.
  
  pulumiInit = pkgs.writeShellScriptBin "pulumi-init" ''
    export HOME=/home/argocd
    
    # Add python to PATH for this script execution
    export PATH=${pythonEnv}/bin:$PATH

    ${pkgs.pulumi}/bin/pulumi login --local
    # Create stack if not exists (ignoring error if it exists)
    ${pkgs.pulumi}/bin/pulumi stack select dev --create || true
    # Ensure kubernetes plugin is installed
    ${pkgs.pulumi}/bin/pulumi plugin install resource kubernetes
  '';

  pulumiGenerate = pkgs.writeShellScriptBin "pulumi-generate" ''
    export HOME=/home/argocd
    export PYTHONPATH=$PYTHONPATH:$(pwd)/crds
    
    # Add python to PATH so Pulumi can find the python3 executable
    export PATH=${pythonEnv}/bin:$PATH

    # Run pulumi up, redirecting output to stderr
    ${pkgs.pulumi}/bin/pulumi up --yes --skip-preview 1>&2
    
    # Concatenate all generated YAML files to stdout
    ${pkgs.gawk}/bin/awk 'FNR==1 && NR!=1 {print "---"} {print}' ./manifests/1-manifest/*.yaml
  '';
in pkgs.dockerTools.buildImage {
  name = "pulumi-cmp-plugin";
  tag = "latest";
  
  config = {
    # Argo CD typically executes commands via /bin/sh or /bin/bash.
    # We set PATH to /bin so it finds sh, bash, and our scripts.
    Env = [
      "PATH=/bin"
      "HOME=/home/argocd"
      "PULUMI_HOME=/home/argocd/.pulumi"
    ];
    
    User = "999";
    WorkingDir = "/home/argocd";
  };
  
  copyToRoot = pkgs.buildEnv {
    name = "image-root";
    paths = [
      # Essential shell environment
      pkgs.bash
      pkgs.coreutils
      pkgs.fakeNss
      
      # Our custom scripts
      pulumiInit
      pulumiGenerate
    ];
    pathsToLink = [ "/bin" "/etc" "/var" "/tmp" ];
  };
  
  runAsRoot = ''
    mkdir -p /home/argocd/.pulumi
    mkdir -p /tmp
    chmod 1777 /tmp
    chown -R 999:999 /home/argocd
  '';
}