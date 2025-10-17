# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None

base_dir = r'C:/Users/Workstation 1/security-testing-framework'

a = Analysis(
    [f'{base_dir}/launcher.py'],
    pathex=[base_dir],
    binaries=[],
    datas=[
        (f'{base_dir}/src', 'src'),
        (f'{base_dir}/resources', 'resources'),
        (f'{base_dir}/config.json', '.'),
    ],
    hiddenimports=[
        # Core Python modules - FIXED: Added ctypes.wintypes
        'tkinter','tkinter.ttk','tkinter.messagebox','tkinter.filedialog',
        'ctypes','ctypes.wintypes','ctypes.util',
        'json','threading','subprocess','pathlib','logging','argparse',
        'datetime','base64','tempfile','shutil','os','sys',
        # Third-party required - FIXED: Included numpy and PIL
        'numpy','PIL','PIL.Image','PIL.ImageDraw','psutil',
        'cryptography','requests','yaml',
        # Pywin32 modules
        'win32api','win32con','win32gui','win32process','win32security',
        'win32file','win32event','win32service','pywintypes','winreg',
        # Application modules with src prefix
        'src','src.core','src.modules','src.gui','src.cli','src.utils',
        'src.core.stealth_engine','src.core.advanced_config',
        'src.modules.comprehensive_test_runner','src.modules.input_monitor',
        'src.modules.system_monitor','src.modules.memory_scanner',
        'src.modules.api_hooks','src.modules.screen_capture_bypass',
        'src.modules.directx_hook','src.modules.test_runner',
        'src.gui.main_window','src.cli.cli_handler',
        'src.utils.report_generator','src.utils.updater',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib','pandas','scipy','test','tests',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SecurityTestingFramework',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Changed to True for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    uac_admin=True,
)
