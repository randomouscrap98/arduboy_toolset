# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['main_gui.py'],
    pathex=[],
    binaries=[],
    datas=[('appresource', 'appresource')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='arduboy_toolset_mac_intel',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='x86_64',
    codesign_identity=None,
    entitlements_file=None,
    icon=['appresource/icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='arduboy_toolset_mac_intel',
)
app = BUNDLE(
    coll,
    name='arduboy_toolset_mac_intel.app',
    icon='appresource/icon.ico',
    bundle_identifier=None,
)
