# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


import os

from pathlib import Path


self_path = Path(os.getcwd()).absolute()
print(str(self_path))
site_packages_path = self_path / Path("venv") / Path("Lib") / Path("site-packages")
print(str(site_packages_path))


a = Analysis(['main.py'],
             pathex=[str(site_packages_path)],
             binaries=[],
             datas=[
             ],
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
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='main',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True )
