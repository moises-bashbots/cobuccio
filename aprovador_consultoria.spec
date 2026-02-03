# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['aprovador_fromtis_api/aprovador_consultoria.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['sqlalchemy', 'zeep', 'requests', 'xmltodict', 'lxml'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='aprovador_consultoria',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

