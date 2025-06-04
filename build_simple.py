#!/usr/bin/env python3
"""
StickyBot Simple Build Script - GitHub Actions Fallback
Robuster Build ohne .spec Datei-Abhängigkeit
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def build_simple():
    """Einfacher, robuster Build für GitHub Actions"""
    
    print("[BUILD] Starte einfachen StickyBot Build...")
    print("="*50)
    
    # Build-Verzeichnisse bereinigen
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    if os.path.exists('build'):
        shutil.rmtree('build')
    
    print("[OK] Build-Verzeichnisse bereinigt")
    
    # PyInstaller direkter Aufruf
    print("[PACK] Erstelle Bot mit PyInstaller...")
    
    try:
        # Einfacher, direkter PyInstaller Aufruf
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--onefile',
            '--windowed',
            '--name=StickyBot',
            '--add-data=src;src',
            '--hidden-import=discord',
            '--hidden-import=discord.ext.commands',
            '--hidden-import=tkinter',
            '--hidden-import=dotenv',
            '--hidden-import=aiohttp',
            '--hidden-import=cryptography',
            '--hidden-import=flask',
            '--hidden-import=requests',
            'main.py'
        ]
        
        # Icon nur hinzufügen wenn vorhanden
        if os.path.exists('icon.ico'):
            cmd.insert(-1, '--icon=icon.ico')
        
        print(f"[CMD] {' '.join(cmd)}")
        
        result = subprocess.run(cmd, check=True)
        print("[OK] PyInstaller Build erfolgreich!")
        
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] PyInstaller Build fehlgeschlagen!")
        print(f"Exit code: {e.returncode}")
        return False
    
    # Überprüfe Ergebnis
    exe_path = Path("dist/StickyBot.exe")
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"[OK] StickyBot.exe erstellt ({size_mb:.1f} MB)")
    else:
        print("[ERROR] StickyBot.exe nicht gefunden!")
        return False
    
    # Minimale Dateien erstellen
    print("[PACK] Erstelle minimale Release-Struktur...")
    
    # data-Ordner mit leeren JSON-Dateien
    data_dir = Path("dist/data")
    data_dir.mkdir(exist_ok=True)
    
    # Leere JSON-Dateien
    (data_dir / "sticky_messages.json").write_text('{}')
    (data_dir / "bot_roles.json").write_text('{}')
    print("[OK] data/ Ordner erstellt")
    
    # README kopieren
    if os.path.exists('README.md'):
        shutil.copy2('README.md', 'dist/')
        print("[OK] README.md kopiert")
    
    # .env entfernen falls vorhanden (für GUI-Setup)
    env_file = Path("dist/.env")
    if env_file.exists():
        env_file.unlink()
        print("[OK] .env entfernt (GUI-Setup aktiviert)")
    
    print("\n[SUCCESS] Einfacher Build erfolgreich!")
    print("Struktur:")
    print("├── StickyBot.exe")
    print("├── data/")
    print("│   ├── sticky_messages.json")
    print("│   └── bot_roles.json")
    print("└── README.md")
    
    return True

if __name__ == "__main__":
    if build_simple():
        print("\n[SUCCESS] Build erfolgreich!")
        sys.exit(0)
    else:
        print("\n[ERROR] Build fehlgeschlagen!")
        sys.exit(1) 