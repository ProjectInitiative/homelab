let
  cdk8s-cli-overlay = import ./cdk8s-cli-patch;
  jsii-patch-overlay = import ./jsii-patch;
in
final: prev:
(cdk8s-cli-overlay final prev) // (jsii-patch-overlay final prev) //{
  python3 = prev.python3.override {
    packageOverrides = pfinal: pprev: {
      cdk8s = pfinal.buildPythonPackage rec {
        pname = "cdk8s";
        version = "2.70.30";

        src = pfinal.fetchPypi {
          inherit pname version;
          sha256 = "sha256:0pb2lymm8fikp3z0rhlxs18ai7lk6z2xb2a46wbwnpi2dylyp92c";
        };

        pyproject = true;
        build-system = with pfinal; [ setuptools_75_3_2 build ]; # Use specific setuptools
        nativeBuildInputs = [ final.nodejs pfinal.setuptools_75_3_2 pfinal.build ]; # Use specific setuptools

        propagatedBuildInputs = with pfinal; [
          constructs
          jsii
          publication
          typeguard
        ];

        doCheck = false;
      };

      # Define a specific setuptools version for constructs
      setuptools_75_3_2 = pprev.setuptools.overrideAttrs (old: {
        version = "75.3.2";
        src = pfinal.fetchPypi {
          pname = "setuptools";
          version = "75.3.2";
          sha256 = "sha256:1xb4jgj7s9wddj571d8f3ca21kc7i3nqs7ic71m5as4b0ghq64rw";
        };
        patches = []; # Remove incompatible patches
      });

      jsii = pfinal.jsii-patched-overlay;
      # Define jsii using the pre-built wheel
      # jsii = pfinal.buildPythonPackage rec {
      #   pname = "jsii";
      #   version = "1.120.0";

      #   src = prev.fetchurl {
      #     url = "https://pypi.org/packages/py3/j/jsii/jsii-1.120.0-py3-none-any.whl";
      #     sha256 = "sha256-W6m4pUIM5m9YsaccpXpFZsZ/BLRpFAvjNb10q7kdXgs="; # Let Nix calculate the hash
      #   };

      #   format = "wheel";

      #   doCheck = false;
      # };

      # Define publication using the pre-built wheel
      publication = pfinal.buildPythonPackage rec {
        pname = "publication";
        version = "0.0.3";

        src = pfinal.fetchPypi {
          pname = pname;
          version = version;
          format = "wheel";
          sha256 = "sha256:1rpv7asi5kbyw6qnvjf0x3rvrnmj7a75r389l7c13g7ya59qhj02";
        };

        format = "wheel";

        doCheck = false;
      };

      # Override typeguard to a compatible version
      typeguard = pfinal.buildPythonPackage rec {
        pname = "typeguard";
        version = "2.13.3";

        src = prev.fetchurl {
          url = "https://pypi.org/packages/py3/t/typeguard/typeguard-2.13.3-py3-none-any.whl";
          sha256 = "sha256-Xj474B6Ifn6vrlr2PR82yEmqqU46ARIJcxKqv6FihPE=";
        };

        format = "wheel";

        doCheck = false;
      };

      # Add build to packageOverrides
      build = pprev.build;

      constructs = pfinal.buildPythonPackage rec {
        pname = "constructs";
        version = "10.4.3"; # Latest version found

        src = pfinal.fetchPypi {
          inherit pname version;
          sha256 = "sha256:181fsl03hajs29qlzy7qvn2awp5f73isgagxl5xayqnb19xnbqxz";
        };

        pyproject = true;
        build-system = with pfinal; [ setuptools_75_3_2 ]; # Use the specific setuptools
        nativeBuildInputs = [ final.nodejs pfinal.setuptools_75_3_2 ]; # Use the specific setuptools

        propagatedBuildInputs = with pfinal; [
          jsii
          publication
          typeguard
        ];

        doCheck = false; # Disable tests for now to get it building
      };
    };
  };
}