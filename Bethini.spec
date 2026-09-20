# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
import sys

block_cipher = None

# This function allows us to add files to directories that need to be included in
# the application's directory in order to function.
def recurseDirs(directory):
    cwd = Path.cwd()
    data = []
    for thedir in directory:
        root_dir = cwd / thedir
        for dir_, _, files in os.walk(root_dir):
            for file_name in files:
                rel_dir = os.path.relpath(dir_, root_dir)
                rel_file = os.path.join(rel_dir, file_name)
                data.append((os.path.join(thedir, rel_file), os.path.join(thedir, rel_dir)))
    # We need to add the icon to the root folder as well.
    data.append(('Icon.ico', '.'))
    return data


a = Analysis(['Bethini.pyw'],
             pathex=[],
             binaries=[],
             datas=recurseDirs(['apps', 'icons']),
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='Bethini',
          debug=True,
          bootloader_ignore_signals=False,
          strip=False,
          upx=False,
          console=False,
          icon='Icon.ico' if sys.platform == 'win32' else None)
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               upx_exclude=[],
               name='Bethini')
