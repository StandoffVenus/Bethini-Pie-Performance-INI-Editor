# Compatibility entry for `nix-build` / `nix-shell` without flakes.
{
  pkgs ? import <nixpkgs> { config.allowUnfree = true; },
}:
pkgs.callPackage ./nix/package.nix { src = ./.; }
