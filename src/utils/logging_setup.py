"""
Logging Setup für Sticky-Bot
"""
import logging
import sys
import os
from datetime import datetime


def safe_print(message):
    """Sichere Print-Funktion"""
    try:
        print(message, flush=True)
    except:
        pass


def setup_debug_logging():
    """Setup für Logging System"""
    try:
        # Log-Level basierend auf Umgebung
        log_level = logging.WARNING  # Nur Warnungen und Fehler
        
        if getattr(sys, 'frozen', False):
            # Production: Minimales Logging
            app_path = os.path.dirname(sys.executable)
        else:
            # Development: Etwas mehr Logging
            current_dir = os.path.dirname(os.path.abspath(__file__))
            app_path = os.path.dirname(os.path.dirname(current_dir))
            log_level = logging.INFO  # Info + Warnings + Errors
        
        # Log-Datei Pfad
        log_dir = os.path.join(app_path, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, 'sticky_bot.log')
        
        # Logging konfigurieren
        logging.basicConfig(
            level=log_level,
            format='[%(asctime)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout) if not getattr(sys, 'frozen', False) else logging.NullHandler()
            ]
        )
        
        return True
        
    except Exception:
        return False 