{ pkgs, pythonEnv }:

let
  cdk8sGenerate = pkgs.writeShellScriptBin "cdk8s-generate" ''
    export HOME=/home/argocd
    export PATH=${pythonEnv}/bin:${pkgs.nodejs_22}/bin:$PATH
    ${pythonEnv}/bin/python main.py 1>&2
    cat dist/*.k8s.yaml
  '';

in pkgs.dockerTools.buildLayeredImage {
  name = "cdk8s-cmp-plugin";
  tag = "latest";

  config = {
    Env = [
      "PATH=/bin"
      "HOME=/home/argocd"
    ];
    User = "999";
    WorkingDir = "/app/generator";
  };

  contents = [
    pkgs.cacert
    pkgs.nodejs_22
    pythonEnv
    pkgs.bash
    pkgs.coreutils
    pkgs.fakeNss
    cdk8sGenerate
  ];

  fakeRootCommands = ''
    mkdir -p ./home/argocd
    mkdir -p ./app/generator
    mkdir -p ./tmp
    chmod 1777 ./tmp
    chown -R 999:999 ./home/argocd
  '';
}
