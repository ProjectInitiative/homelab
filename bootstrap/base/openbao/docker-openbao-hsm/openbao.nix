{
  pkgs ? import <nixpkgs> { },
}:

let
  # Override the default openbao package to enable HSM support.
  # This assumes `openbao` is available in your nixpkgs channel
  # and that it has a `withHsm` option.
  openbao = pkgs.openbao.override { withHsm = true; };

in pkgs.stdenv.mkDerivation rec {
  pname = "openbao-hsm-env";
  version = "1.0";

  src = ./.;

  nativeBuildInputs = [ pkgs.makeWrapper ];

  propagatedBuildInputs = [
    openbao
    pkgs.opensc # for pkcs11-tool
    pkgs.tpm2-pkcs11
    pkgs.softhsm
    pkgs.dumb-init
    pkgs.su-exec
    pkgs.bashInteractive
    pkgs.gnugrep
    pkgs.coreutils
    pkgs.gawk
  ];

  installPhase = ''
    runHook preInstall
    mkdir -p $out/bin $out/usr/lib
    cp ${./entrypoint.sh} $out/bin/entrypoint.sh
    chmod +x $out/bin/entrypoint.sh

    # Create a stable symlink for the PKCS#11 library
    ln -s "${pkgs.tpm2-pkcs11}/lib/libtpm2_pkcs11.so" "$out/usr/lib/libtpm2_pkcs11.so"
    ln -s "${pkgs.softhsm}/lib/libsofthsm2.so" "$out/usr/lib/libsofthsm2.so"


    substituteInPlace $out/bin/entrypoint.sh \
      --replace '@dumb-init@' "${pkgs.dumb-init}/bin/dumb-init" \
      --replace '@shell@' "${pkgs.bashInteractive}/bin/sh"

    wrapProgram $out/bin/entrypoint.sh \
      --prefix PATH : ${pkgs.lib.makeBinPath propagatedBuildInputs}
    runHook postInstall
  '';

  meta = with pkgs.lib; {
    description = "OpenBao with HSM support and tools";
    license = licenses.mit;
    platforms = platforms.linux;
  };
}
