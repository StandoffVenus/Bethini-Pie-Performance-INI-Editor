{
  description = "Bethini Pie — INI editor for Bethesda game configuration";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs =
    { self, nixpkgs }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "x86_64-darwin"
        "aarch64-darwin"
      ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
    in
    {
      overlays.default = final: _prev: {
        bethini-pie = final.callPackage ./nix/package.nix { src = self; };
      };

      packages = forAllSystems (
        system:
        let
          pkgs = import nixpkgs {
            inherit system;
            overlays = [ self.overlays.default ];
            config.allowUnfree = true;
          };
        in
        {
          default = pkgs.bethini-pie;
          bethini-pie = pkgs.bethini-pie;
        }
      );

      apps = forAllSystems (system: {
        default = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/bethini";
        };
      });

      devShells = forAllSystems (
        system:
        let
          pkgs = import nixpkgs {
            inherit system;
            overlays = [ self.overlays.default ];
            config.allowUnfree = true;
          };
        in
        {
          default = pkgs.mkShell {
            packages = [
              pkgs.bethini-pie.pythonEnv
              pkgs.pyinstaller
              pkgs.git
            ];
            shellHook = ''
              echo "Bethini Pie Nix shell"
              echo "  run:    python Bethini.pyw"
              echo "  tests:  python -m unittest tests.test_platform_support -v"
            '';
          };
        }
      );

      formatter = forAllSystems (system: nixpkgs.legacyPackages.${system}.nixfmt-rfc-style);
    };
}
