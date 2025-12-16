{ lib, buildGoModule, fetchFromGitHub }:

buildGoModule {
  pname = "korb";
  version = "v2.0.0-unstable"; # This version is derived from the upstream go.mod, typically it's good to keep it in sync

  src = fetchFromGitHub {
    owner = "BeryJu";
    repo = "korb";
    rev = "a1b862567f07e638d9f9dc9e646ef58ac80fbfce";
    hash = "sha256-jznXK+YlPjglafrTA1jlCuxKkZSetgk9GeY0FWxnHy4=";
  };

  vendorHash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="; # Placeholder, will be replaced by the correct hash after first build

  subPackages = [ "." ]; # Assuming main.go is in root

  meta = with lib; {
    description = "Korb: Kubernetes PVC Migration Tool";
    homepage = "https://github.com/BeryJu/korb";
    license = licenses.mit; 
    maintainers = with maintainers; [ ];
  };
}
