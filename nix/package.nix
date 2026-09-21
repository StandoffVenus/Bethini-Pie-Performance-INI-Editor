{
  lib,
  stdenvNoCC,
  python312,
  makeWrapper,
  fetchurl,
  gnutar,
  gzip,
  src,
}:

let
  python3 = python312;
  ttkbootstrap = python3.pkgs.callPackage ./ttkbootstrap.nix { };

  pythonEnv = python3.withPackages (
    ps: [
      ps.pillow
      ps.simpleeval
      ps.tkinter
      ttkbootstrap
    ]
  );

  plugins = {
    "Fallout 4" = fetchurl {
      url = "https://github.com/DoubleYouC/Bethini-Pie-Fallout-4-Plugin/archive/7f327ea8491fa18e9a072d9aadf6309ea9c5425b.tar.gz";
      hash = "sha256-5SJh6M2hA0PGf2xnwIkGLGJ+ThmgdlrgyOYA2wyiqDY=";
    };
    "Fallout New Vegas" = fetchurl {
      url = "https://github.com/DoubleYouC/Bethini-Pie-Fallout-New-Vegas-Plugin/archive/7a4075201788359c97a0861993974a0ec983a17e.tar.gz";
      hash = "sha256-BC3rYKYaFN/boSQuBzg6Ju/Mru86YbnwtfTKG7SzbYU=";
    };
    "Skyrim Special Edition" = fetchurl {
      url = "https://github.com/DoubleYouC/Bethini-Pie-Skyrim-Special-Edition-Plugin/archive/74bbebaa0ac8c974a2cb1db7b0f4b7892e47d956.tar.gz";
      hash = "sha256-6v8vUK43PuvZPPeyX6SshRdCyiVcV586bxYzqzeweZ4=";
    };
    "Starfield" = fetchurl {
      url = "https://github.com/DoubleYouC/Bethini-Pie-Starfield-Plugin/archive/909ea686c164b6295201bdda11a0826688643a6b.tar.gz";
      hash = "sha256-7PX/504XMREItVZ1y2g/sky3QA7jeth3ziljESDxCkU=";
    };
  };

in
stdenvNoCC.mkDerivation {
  pname = "bethini-pie";
  version = "4.18";

  src = lib.cleanSource src;

  nativeBuildInputs = [
    makeWrapper
    gnutar
    gzip
  ];

  nativeCheckInputs = [ pythonEnv ];

  doCheck = true;

  checkPhase = ''
    runHook preCheck
    python -m unittest tests.test_platform_support -v
    runHook postCheck
  '';

  installPhase = ''
    runHook preInstall

    share=$out/share/bethini-pie
    mkdir -p "$share"

    cp Bethini.pyw changelog.txt LICENSE.txt README.md "$share/"
    cp -r lib icons fonts "$share/"

    mkdir -p "$share/apps"
    ${lib.concatStringsSep "\n" (
      lib.mapAttrsToList (name: tarball: ''
        mkdir -p "$share/apps/${name}"
        tar -xzf ${tarball} --strip-components=1 -C "$share/apps/${name}"
      '') plugins
    )}

    mkdir -p $out/bin
    makeWrapper ${pythonEnv}/bin/python $out/bin/bethini \
      --add-flags "$share/Bethini.pyw"

    mkdir -p $out/share/pixmaps $out/share/applications
    cp icons/Icon.png $out/share/pixmaps/bethini-pie.png
    cat > $out/share/applications/bethini-pie.desktop <<EOF
    [Desktop Entry]
    Type=Application
    Name=Bethini Pie
    Comment=INI editor for Bethesda game configuration
    Exec=bethini
    Icon=bethini-pie
    Terminal=false
    Categories=Utility;Game;
    EOF

    runHook postInstall
  '';

  passthru = {
    inherit pythonEnv ttkbootstrap;
  };

  meta = {
    description = "INI editor for advanced Bethesda game configuration";
    homepage = "https://www.nexusmods.com/site/mods/631/";
    license = lib.licenses.cc-by-nc-sa-40;
    mainProgram = "bethini";
    platforms = lib.platforms.unix;
  };
}
