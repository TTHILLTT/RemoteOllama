# PyInstaller spec for Windows/Linux packaging
# Usage: pyinstaller RemoteOllama.spec

# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

block_cipher = None

_a = Analysis(
    ['app/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('app/resources/qml/*.qml', 'resources/qml'),
        ('app/resources/qml/qmldir', 'resources/qml'),
        ('app/resources/icons/*', 'resources/icons'),
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtQml',
        'PySide6.QtQuick',
        'PySide6.QtQuickControls2',
        'PySide6.QtQuickLayouts',
        'httpx',
        'httpcore',
        'markdown',
        'pygments',
        'sqlite3',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'unittest',
        'email',
        'html',
        'xml',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

_pyz = PYZ(_a.pure, _a.zipped_data, cipher=block_cipher)

_exe = EXE(
    _pyz,
    _a.scripts,
    _a.binaries,
    _a.zipfiles,
    _a.datas,
    [],
    name='RemoteOllama',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app/resources/icons/app.ico' if sys.platform == 'win32' else None,
)
