final: prev: {
  python3 = prev.python3.override {
    packageOverrides = pfinal: pprev: {
      pulumi-kubernetes = pfinal.buildPythonPackage rec {
        pname = "pulumi-kubernetes";
        version = "4.24.0";
        format = "wheel";

        src = pfinal.fetchPypi {
          pname = "pulumi_kubernetes";
          inherit version;
          format = "wheel";
          dist = "py3";
          python = "py3";
          sha256 = "d8514c6116be369e23cb28a2c77f9bcc707696564e0670268a838ec62139f76c";
        };

        propagatedBuildInputs = with pfinal; [
          pulumi
          parver
          semver
        ];

        doCheck = false;
      };
    };
  };
}
