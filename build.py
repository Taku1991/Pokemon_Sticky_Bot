#!/usr/bin/env python3
"""
StickyBot Build Script
Erstellt minimales Release-Paket 
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def safe_print(message):
    """Sichere Print-Funktion für Unicode-Zeichen (GitHub Actions kompatibel)"""
    try:
        print(message)
    except UnicodeEncodeError:
        # Fallback: Entferne Unicode-Zeichen und ersetze mit ASCII
        safe_message = message.encode('ascii', 'ignore').decode('ascii')
        if not safe_message.strip():
            # Wenn alles Unicode war, verwende ASCII-Alternative
            safe_message = message.replace('🚀', '[BUILD]').replace('✅', '[OK]').replace('❌', '[ERROR]').replace('📦', '[PACK]').replace('🗑️', '[CLEAN]').replace('📁', '[COPY]').replace('🎉', '[SUCCESS]')
            safe_message = safe_message.encode('ascii', 'ignore').decode('ascii')
        print(safe_message)

def clean_build_dirs():
    """Bereinigt alte Build-Verzeichnisse"""
    dirs_to_clean = ['build', 'dist']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            safe_print(f"[CLEAN] Bereinige {dir_name}/...")
            shutil.rmtree(dir_name)
    
    safe_print("[OK] Build-Verzeichnisse bereinigt")

def build_bot():
    """Erstellt minimales Release-Paket"""
    
    safe_print("[BUILD] StickyBot Minimal Build wird gestartet...")
    safe_print("="*50)
    
    # Bereinigung
    clean_build_dirs()
    
    # PyInstaller mit spec-Datei ausführen
    safe_print("\n[PACK] Erstelle Bot mit PyInstaller...")
    
    try:
        # Build mit spec-Datei (erstellt beide Versionen)
        result = subprocess.run([
            sys.executable, '-m', 'PyInstaller', 
            '--clean',
            'bot.spec'
        ], check=True, capture_output=True, text=True)
        
        safe_print("[OK] PyInstaller Build erfolgreich!")
        
    except subprocess.CalledProcessError as e:
        safe_print(f"[ERROR] PyInstaller Build fehlgeschlagen!")
        safe_print(f"Fehler: {e}")
        safe_print(f"Output: {e.stdout}")
        safe_print(f"Error: {e.stderr}")
        return False
    
    # Überprüfe ob OneFile Version erstellt wurde
    onefile_path = Path("dist/StickyBot.exe")
    debug_path = Path("dist/debug/StickyBot_Console.exe")
    
    safe_print("\n[INFO] Build-Ergebnisse:")
    safe_print("-" * 30)
    
    if onefile_path.exists():
        size_mb = onefile_path.stat().st_size / (1024 * 1024)
        safe_print(f"[OK] Haupt-Version: {onefile_path} ({size_mb:.1f} MB)")
    else:
        safe_print(f"[ERROR] Haupt-Version nicht gefunden: {onefile_path}")
        return False
    
    if debug_path.exists():
        safe_print(f"[OK] Debug-Version verfügbar: {debug_path}")
    
    # Erstelle minimales Release-Paket entsprechend README
    safe_print("\n[PACK] Erstelle minimales Release-Paket...")
    create_minimal_release_package()
    
    safe_print("\n[SUCCESS] Minimaler Build erfolgreich abgeschlossen!")
    safe_print("="*50)
    safe_print("\n[INFO] Erstellte ultra-minimale Struktur:")
    safe_print("• StickyBot.exe (Hauptprogramm)")
    safe_print("• data/ (Bot-Daten)")
    safe_print("• README.md (Anleitung)")
    safe_print("\n[INFO] Keine .env → GUI-Setup startet automatisch!")
    safe_print("[INFO] Release-ready: dist/ Ordner kann direkt verwendet werden!")
    
    return True

def create_minimal_release_package():
    """Erstellt minimales Paket entsprechend README-Struktur"""
    
    safe_print("[PACK] Erstelle minimale Ordnerstruktur...")
    
    # Nur die essentiellen Dateien für ein sauberes Release
    
    # 1. data-Ordner mit leeren JSON-Dateien erstellen
    safe_print("[COPY] Erstelle data-Ordner...")
    dist_data = Path("dist/data")
    if not dist_data.exists():
        dist_data.mkdir()
    
    # Leere JSON-Dateien erstellen
    json_files = {
        'sticky_messages.json': '{}',
        'bot_roles.json': '{}'
    }
    
    for filename, content in json_files.items():
        json_path = dist_data / filename
        with open(json_path, 'w', encoding='utf-8') as f:
            f.write(content)
        safe_print(f"[OK] {filename} erstellt")
    
    # 2. README.md kopieren
    safe_print("[COPY] Kopiere README.md...")
    if os.path.exists('README.md'):
        shutil.copy2('README.md', 'dist/')
        safe_print("[OK] README.md kopiert")
    
    # 3. Alle überflüssigen Dateien entfernen
    safe_print("[CLEAN] Entferne alle überflüssigen Dateien...")
    files_to_remove = [
        'dist/requirements.txt',
        'dist/icon.ico',
        'dist/StickyBot.png',
        'dist/start.bat',
        'dist/.env'  # Wichtig: .env entfernen damit GUI-Setup startet!
    ]
    
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            os.remove(file_path)
            safe_print(f"[OK] {file_path} entfernt")
    
    # Debug-Ordner auch entfernen für sauberes Release
    debug_dir = Path("dist/debug")
    if debug_dir.exists():
        shutil.rmtree(debug_dir)
        safe_print("[OK] debug/ Ordner entfernt")
    
    # 4. Finale minimale Struktur anzeigen
    safe_print("\n[INFO] Finale minimale Ordnerstruktur:")
    safe_print("dist/")
    safe_print("├── StickyBot.exe")
    safe_print("├── data/")
    safe_print("│   ├── sticky_messages.json")
    safe_print("│   └── bot_roles.json")
    safe_print("└── README.md")
    safe_print("\n[INFO] Keine .env → GUI-Setup startet automatisch!")
    safe_print("[INFO] Kein debug/ → Sauberes Release für Endbenutzer!")
    
    safe_print("[OK] Minimales Release-Paket erstellt")

if __name__ == "__main__":
    if build_bot():
        safe_print("\n[SUCCESS] Build erfolgreich!")
        sys.exit(0)
    else:
        safe_print("\n[ERROR] Build fehlgeschlagen!")
        sys.exit(1) 