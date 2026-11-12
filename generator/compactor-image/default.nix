let
  pkgs = import <nixpkgs> {};
in
pkgs.recurseIntoAttrs {
  compactor-image = import ./image.nix { inherit pkgs; };
}
