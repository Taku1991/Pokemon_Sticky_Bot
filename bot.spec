# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None

# Aktueller Pfad
current_path = os.path.abspath('.')

a = Analysis(
    ['main.py'],
    pathex=[current_path],
    binaries=[],
    datas=[
        # Alle src Module einbinden
        ('src', 'src'),
        # Icon für GUI
        ('icon.ico', '.'),
        # Requirements für Referenz
        ('requirements.txt', '.'),
    ],
    hiddenimports=[
        'discord',
        'discord.ui', 
        'discord.ext.commands',
        'discord.app_commands',
        'dotenv',
        'tkinter',
        'tkinter.messagebox',
        'tkinter.simpledialog',
        'tkinter.ttk',
        'tkinter.filedialog',
        'aiohttp',
        'asyncio',
        'threading',
        'json',
        'logging',
        'traceback',
        'sys',
        'os',
        're',
        'datetime',
        # OAuth2 und Web-Authentifizierung
        'flask',
        'requests',
        'webbrowser',
        'urllib.parse',
        'base64',
        'hashlib',
        'hmac',
        'secrets',
        'uuid',
        'platform',
        'subprocess',
        # Sichere Verschlüsselung
        'cryptography',
        'cryptography.fernet',
        'cryptography.hazmat.primitives',
        'cryptography.hazmat.primitives.kdf.pbkdf2',
        'cryptography.hazmat.primitives.hashes',
        # Core Bot-Module
        'src',
        'src.core',
        'src.core.bot_manager',
        # Bot Commands/Cogs
        'src.cogs',
        'src.cogs.admin',
        'src.cogs.sticky',
        # Utils
        'src.utils',
        'src.utils.discord_auth',
        'src.utils.discord_oauth',
        'src.utils.token_setup',
        'src.utils.permissions',
        'src.utils.secure_storage',
        'src.utils.path_manager',
        'src.utils.logging_setup',
        'src.utils.db_manager',
        'src.utils.exceptions',
        # UI Komponenten
        'src.ui',
        'src.ui.status_window',
        'src.ui.settings_window',
        'src.ui.sticky_dialog',
        'src.ui.modals',
        'src.ui.tabs',
        # Config
        'src.config',
        # Tkinter spezifische Module
        '_tkinter',
        'tkinter.constants',
        # PIL/Pillow für Bilder
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ONEFILE Version (GUI-Mode für besseres tkinter)
exe_onefile = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='StickyBot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI-Mode für tkinter
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(current_path, 'icon.ico')
)

# ONEDIR Version (für Debug mit Console)
exe_onedir = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='StickyBot_Console',
    debug=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(current_path, 'icon.ico')
)

coll = COLLECT(
    exe_onedir,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='debug'
)