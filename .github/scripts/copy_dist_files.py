#!/usr/bin/env python3
"""Copy runtime files next to the PyInstaller binary in dist/.

PyInstaller onefile unpacks to a temp dir, but Bethini resolves apps/icons/fonts
relative to the executable. Those files must sit beside the built binary on every OS.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / "dist"


def copy_file(src: Path, dst: Path) -> None:
    if not src.is_file():
        print(f"skip missing file: {src}", file=sys.stderr)
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def copy_tree(src: Path, dst: Path, *, drop_src_dir: bool = False) -> None:
    if not src.exists():
        print(f"skip missing directory: {src}", file=sys.stderr)
        return
    shutil.copytree(src, dst, dirs_exist_ok=True)
    extra = dst / "src"
    if drop_src_dir and extra.exists():
        shutil.rmtree(extra)


def main() -> None:
    DIST.mkdir(parents=True, exist_ok=True)

    for name in ("LICENSE.txt", "README.md", "changelog.txt", "Icon.ico"):
        copy_file(ROOT / name, DIST / name)

    copy_tree(ROOT / "icons", DIST / "icons")
    copy_tree(ROOT / "fonts" / "Comfortaa", DIST / "fonts" / "Comfortaa")

    apps = ROOT / "apps"
    dist_apps = DIST / "apps"
    dist_apps.mkdir(parents=True, exist_ok=True)
    if not apps.is_dir():
        return

    for game in sorted(apps.iterdir()):
        if not game.is_dir() or game.name.startswith("."):
            continue
        dest = dist_apps / game.name
        dest.mkdir(parents=True, exist_ok=True)
        for fname in ("Bethini.json", "settings.json"):
            copy_file(game / fname, dest / fname)
        images = game / "images"
        if images.exists():
            copy_tree(images, dest / "images", drop_src_dir=True)


if __name__ == "__main__":
    main()
