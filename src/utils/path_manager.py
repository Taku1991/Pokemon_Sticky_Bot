"""
Pfad-Management für Sticky-Bot
Behandelt Pfade für sowohl Development- als auch Production-Umgebung
"""
import os
import sys


def get_application_path():
    """
    Ermittelt den korrekten Anwendungspfad für beide Modi:
    - Development: Projektverzeichnis
    - Production: Verzeichnis der .exe
    """
    try:
        if getattr(sys, 'frozen', False):
            # Production: PyInstaller Bundle
            return os.path.dirname(os.path.abspath(sys.executable))
        else:
            # Development: Script Mode
            return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
    except Exception:
        # Fallback
        return os.getcwd()


def setup_paths():
    """
    Initialisiert alle notwendigen Pfade und Verzeichnisse
    
    Returns:
        str: Anwendungspfad oder None bei Fehler
    """
    try:
        app_path = get_application_path()
        
        # Arbeitsverzeichnis setzen
        os.chdir(app_path)
        
        # Python-Pfad erweitern (nur für Development)
        if not getattr(sys, 'frozen', False):
            if app_path not in sys.path:
                sys.path.insert(0, app_path)
        
        # Notwendige Verzeichnisse erstellen
        directories = ['data', 'logs']
        for directory in directories:
            dir_path = os.path.join(app_path, directory)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
        
        return app_path
        
    except Exception:
        return None 