# shim.nix
{
  pkgs ? import <nixpkgs> { },
}:
let
  dependencies = [
    pkgs.bashInteractive
    pkgs.coreutils # for sleep
    pkgs.procps    # for kill, pidof
  ];
in
pkgs.stdenv.mkDerivation {
  pname = "openbao-helm-shim";
  version = "1.0";
  src = ./.;
  nativeBuildInputs = [ pkgs.makeWrapper ];
  installPhase = ''
    mkdir -p $out/bin
    cp ${./shim.sh} $out/bin/sh
    chmod +x $out/bin/sh
    wrapProgram $out/bin/sh \
      --prefix PATH : ${pkgs.lib.makeBinPath dependencies}
  '';
}
