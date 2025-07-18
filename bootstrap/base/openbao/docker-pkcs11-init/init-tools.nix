{
  pkgs ? import <nixpkgs> { },
}:

pkgs.stdenv.mkDerivation rec {
  pname = "tpm-init-tools";
  version = "1.0";

  src = ./.;

  nativeBuildInputs = [ pkgs.makeWrapper ];
  propagatedBuildInputs = [
    pkgs.bashInteractive
    pkgs.tpm2-tools
    pkgs.tpm2-pkcs11
    pkgs.opensc
    pkgs.softhsm
    pkgs.openssl
    pkgs.gnugrep
    pkgs.coreutils
    pkgs.findutils
  ];

  installPhase = ''
    runHook preInstall
    install -d $out/bin
    install -Dm755 $src/init-script.sh $out/bin/init-script

    # ADD THIS: Replace the placeholder with the real library path.
    substituteInPlace $out/bin/init-script \
      --replace "@tpm_pkcs11_lib@" "${pkgs.tpm2-pkcs11}/lib/libtpm2_pkcs11.so"

    substituteInPlace $out/bin/init-script \
      --replace "@softhsm2_lib@" "${pkgs.softhsm}/lib/libsofthsm2.so"

    # The wrapProgram is still needed to find the 'pkcs11-tool' executable.
    wrapProgram $out/bin/init-script \
      --prefix PATH : ${pkgs.lib.makeBinPath propagatedBuildInputs}

    runHook postInstall
  '';

  meta = with pkgs.lib; {
    description = "A tool to check and initialize a TPM 2.0 device for PKCS#11 use.";
    license = licenses.mit;
    platforms = platforms.linux;
  };
}
