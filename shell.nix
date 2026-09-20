{
  pkgs ? import <nixpkgs> { config.allowUnfree = true; },
}:
let
  bethini-pie = pkgs.callPackage ./nix/package.nix { src = ./.; };
in
pkgs.mkShell {
  packages = [
    bethini-pie.pythonEnv
    pkgs.pyinstaller
    pkgs.git
  ];

  shellHook = ''
    echo "Bethini Pie Nix shell"
    echo "  run:    python Bethini.pyw"
    echo "  tests:  python -m unittest tests.test_platform_support -v"
  '';
}
