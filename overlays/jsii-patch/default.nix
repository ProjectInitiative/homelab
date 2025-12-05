final: prev:

let
  version = "1.120.0";
  
  # 1. Source Code
  jsiiSrc = prev.fetchFromGitHub {
    owner = "aws";
    repo = "jsii";
    rev = "v${version}"; 
    sha256 = "sha256-shkqL+eHRJXVKXvbJf+nXqe8fAMuBP1eoH2ltO8KfhI="; 
  };

  # 2. Yarn Dependencies (Nix helper)
  offlineCache = prev.fetchYarnDeps {
    yarnLock = "${jsiiSrc}/yarn.lock";
    hash = "sha256-FMUY/0djvBJ54APDTOVKdfCGuQvEXbgZi9LQNYi/3RM="; 
  };

in
{
  # We use buildPythonPackage so it acts like a normal python lib
  jsii-patched = prev.python3.pkgs.buildPythonPackage rec {
    pname = "jsii";
    inherit version;
    src = jsiiSrc;

    format = "pyproject"; # We will build via setup.py

    # 1. APPLY YOUR PATCH HERE
    patches = [
      # ./jsii-cleanup.patch
    ];

    # 2. SETUP YARN CACHE AUTOMATICALLY
    yarnOfflineCache = offlineCache;

    nativeBuildInputs = [
      # The Hooks do the heavy lifting for cache setup
      prev.yarnConfigHook
      prev.yarnBuildHook 
      
      final.nodejs
      prev.yarn
      prev.python3.pkgs.setuptools
      prev.python3.pkgs.wheel
      prev.git

      prev.util-linux

      prev.python3.pkgs.setuptools
      prev.python3.pkgs.wheel
      prev.python3.pkgs.pip
    ];

    pipInstallFlags = [ "--no-build-isolation" ];

    # Skip tests, they need network access
    env = {
      PIP_NO_BUILD_ISOLATION = "false"; # Actually, usually better to let nix handle it via deps
      # But since we have a custom preBuild, we might need to be explicit.
      # Let's try the standard way first (nativeBuildInputs + format="pyproject")
      SKIP_TESTS = 1;
      CI = "true";
      NX_DAEMON = "false"; 
      # Sometimes helps to explicitly set terminal width so it doesn't query ioctl
      COLUMNS = "80"; 
      CODEBUILD_RESOLVED_SOURCE_VERSION = "192dc88de19a49bf03037a66cb194e3263fdaa03"; 
    };


    # 3. HYBRID BUILD LOGIC
    # We disable the default yarnBuildHook behavior because it would try to 
    # install a Node app. We only want it to *compile* the JS.
    dontYarnBuild = true; 
    dontYarnInstall = true;

    postPatch = ''
      # 1. Neuter Java
      echo "#!/bin/sh" > packages/@jsii/java-runtime/generate.sh
      echo "echo 'Skipping Java Generate'" >> packages/@jsii/java-runtime/generate.sh
      echo "exit 0" >> packages/@jsii/java-runtime/generate.sh
      chmod +x packages/@jsii/java-runtime/generate.sh

      # 2. Neuter Go
      mkdir -p packages/@jsii/go-runtime/build-tools
      echo "console.log('Skipping Go Build');" > packages/@jsii/go-runtime/build-tools/gen.js
      
      # 3. Neuter Dotnet (UPDATED)
      # Fix the generate.sh script which is failing with exit code 127
      echo "#!/bin/sh" > packages/@jsii/dotnet-runtime/generate.sh
      echo "echo 'Skipping Dotnet Generate'" >> packages/@jsii/dotnet-runtime/generate.sh
      echo "exit 0" >> packages/@jsii/dotnet-runtime/generate.sh
      chmod +x packages/@jsii/dotnet-runtime/generate.sh

      # Also neuter build.sh if it exists, just in case
      if [ -f packages/@jsii/dotnet-runtime/build.sh ]; then
        echo "#!/bin/sh" > packages/@jsii/dotnet-runtime/build.sh
        echo "exit 0" >> packages/@jsii/dotnet-runtime/build.sh
        chmod +x packages/@jsii/dotnet-runtime/build.sh
      fi

      # 4. Fix shebangs
      patchShebangs .
      substituteInPlace packages/@jsii/python-runtime/requirements.txt \
        --replace-fail "setuptools~=80.3" "setuptools" || true
    '';
    # In preBuild, we manually trigger the JS compilation.
    # Once that finishes, we cd into the python directory.
    # The default buildPythonPackage logic then takes over and builds the wheel
    # using the just-compiled JS assets.
    preBuild = ''
      echo "--- Setting up Dummy Tools to Bypass Missing Runtimes ---"
      mkdir -p dummy-tools
      
      # Create a fake 'mvn' (Java)
      echo '#!/bin/sh' > dummy-tools/mvn
      echo 'echo "Fake mvn called - returning success"' >> dummy-tools/mvn
      echo 'exit 0' >> dummy-tools/mvn
      chmod +x dummy-tools/mvn

      # Create a fake 'dotnet' (.NET)
      echo '#!/bin/sh' > dummy-tools/dotnet
      echo 'echo "Fake dotnet called - returning success"' >> dummy-tools/dotnet
      echo 'exit 0' >> dummy-tools/dotnet
      chmod +x dummy-tools/dotnet
      
      # Create a fake 'go' (Golang)
      echo '#!/bin/sh' > dummy-tools/go
      echo 'echo "Fake go called - returning success"' >> dummy-tools/go
      echo 'exit 0' >> dummy-tools/go
      chmod +x dummy-tools/go

      # Add dummy-tools to the front of PATH
      export PATH=$PWD/dummy-tools:$PATH

      echo "--- Compiling TypeScript Kernel ---"
      
      # "Fake TTY" Hack
      # 'script' creates a pseudo-terminal, tricking nx into thinking it's interactive.
      # -e : Return the exit code of the command (critical for failing on build errors)
      # -c : The command to run
      # /dev/null : Discard the typescript log file (we only want stdout)
      # This skips the Java/Go/Dotnet builds that are failing.

      # We use the local lerna binary directly to avoid npx network calls.
      # --scope: Only build python-runtime
      # --include-dependencies: Build kernel/spec/etc that python needs
      # --stream: Print output immediately so we see what's happening
      
      script -e -c "./node_modules/.bin/lerna run build \
        --scope @jsii/python-runtime \
        --include-dependencies \
        --stream" /dev/null
      
      # script -e -c "npx lerna run build --scope @jsii/python-runtime --include-dependencies --stream" /dev/null

      echo "--- Switching to Python Runtime Directory ---"
      cd packages/@jsii/python-runtime      
    '';

    # buildPythonPackage automatically handles the `installPhase` 
    # (running `setup.py bdist_wheel` and `pip install`), 
    # so we don't need to write one manually!
  };
}