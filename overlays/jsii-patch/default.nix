final: prev: # 1. Arguments must go first so 'prev' is available in the 'let' block

let
  version = "1.120.0";
  # Now this works because 'prev' is in scope
  jsii-ts-compiler = prev.nodePackages.jsii; 
in
{
  jsii-patched = prev.stdenv.mkDerivation rec {
    pname = "jsii";
    inherit version;

    # Fetch the *source* code for jsii
    src = prev.fetchFromGitHub {
      owner = "aws";
      repo = "jsii";
      rev = "v${version}"; 
      sha256 = "sha256-r0fHh2g/Y8nI6e8vKk0j2w7R8Q5f9gY2c3v4T1i5J0A="; 
    };

    patches = [
      # ./jsii-cleanup.patch
    ];

    nativeBuildInputs = [
      final.nodejs
      prev.yarn
      final.makeWrapper
      prev.python3.pkgs.wheel
      prev.python3.pkgs.setuptools
    ];

    # Note: 'yarn install' requires network access, which is blocked in Nix builds.
    # You will likely hit an error here unless you use 'fetchYarnDeps' or 'yarn2nix'.
    # For now, this is the syntax fix you asked for:
    buildPhase = ''
      export HOME=$(mktemp -d)
      
      # Try to install dependencies (may fail due to sandbox)
      ${prev.yarn.bin}/yarn install --frozen-lockfile --ignore-scripts

      # This is where you would normally run the build
      # ${prev.yarn.bin}/yarn build
    '';

    installPhase = ''
      # Navigate to the python runtime directory within the monorepo
      cd packages/@jsii/python-runtime

      # Build the wheel
      ${prev.python3.pkgs.python}/bin/python setup.py bdist_wheel

      # Install the wheel
      ${prev.python3.pkgs.pip}/bin/pip install dist/*.whl --prefix=$out
    '';
  };
}