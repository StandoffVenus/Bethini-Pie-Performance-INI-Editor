# Bethini Pie

## About
Bethini Pie is an INI editor designed to allow advanced customization of game configuration settings.

## Command-line Options

`--noBackups` - does not create any backup files or directories

## Resources
- Official Download Page on Nexus Mods: https://www.nexusmods.com/site/mods/631/
- Bethini Support on STEP Forums: https://stepmodifications.org/forum/forum/200-bethini-support/

## Development
- This project requires Python >= 3.11
- For required pip packages, see `requirements.txt`

### Nix

Build and run with flakes:

```bash
nix build
./result/bin/bethini
# or
nix run
```

Development shell (Python + Tk, Pillow, simpleeval, ttkbootstrap):

```bash
nix develop
python Bethini.pyw
```

Without flakes, using your channel's `nixpkgs`:

```bash
nix-build
nix-shell
```

The package overlay is `overlays.default` (`pkgs.bethini-pie`). The license is CC BY-NC-SA 4.0, so unfree packages must be allowed (`config.allowUnfree`). The flake already sets that for `nix build` / `nix run` / `nix develop`.