{ lib, buildGoModule, fetchFromGitHub }:

buildGoModule {
  pname = "korb";
  version = "v2.0.0-unstable"; # This version is derived from the upstream go.mod, typically it's good to keep it in sync

  src = fetchFromGitHub {
    owner = "BeryJu";
    repo = "korb";
    rev = "6b2f2ad63a9e02d78ffbebccc8a3f3fd6ac09346";
    hash = "sha256-E+5QbDinmxydspwYKhr5ufBf53cb8W1Q2Dlq0MujNH4=";
  };

  vendorHash = "sha256-Qo+YRHe58bJvPTSlZkUS09neNmj+ucDMoJQsYCdqQbE=";

  subPackages = [ "." ]; # Assuming main.go is in root

  meta = with lib; {
    description = "Korb: Kubernetes PVC Migration Tool";
    homepage = "https://github.com/BeryJu/korb";
    license = licenses.mit; 
    maintainers = with maintainers; [ ];
  };
}
