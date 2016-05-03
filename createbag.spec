# -*- mode: python -*-
a = Analysis(['createbag.py'],
             pathex=['c:\\Users\\Alex\\Dropbox\\Documents\\SFU\\archives\\createbag'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='createbag.exe',
          debug=False,
          strip=None,
          upx=True,
          console=False )
