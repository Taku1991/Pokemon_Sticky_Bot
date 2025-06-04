"""
Sticky-Bot - Discord Bot mit Sticky Messages
GUI-Version mit OAuth-Authentifizierung
"""
import os
import sys

# Setup für korrekte Pfade
try:
    from src.utils.path_manager import setup_paths
    app_path = setup_paths()
    if not app_path:
        print("❌ Pfad-Setup fehlgeschlagen")
        sys.exit(1)
except ImportError as e:
    print(f"❌ Import-Fehler: {e}")
    sys.exit(1)

# Logging Setup
try:
    from src.utils.logging_setup import setup_debug_logging
    setup_debug_logging()
except ImportError:
    pass

# Main GUI
try:
    from src.ui.status_window import BotStatusWindow
    from src.core.bot_manager import BotManager
    
    def main():
        """Hauptfunktion - Startet die GUI"""
        try:
            # GUI-Fenster erstellen
            status_window = BotStatusWindow()
            
            # Bot Manager erstellen und verknüpfen
            bot_manager = BotManager(status_window)
            status_window.bot_manager = bot_manager
            
            # GUI starten
            status_window.run()
            
        except Exception as e:
            try:
                import tkinter as tk
                from tkinter import messagebox
                root = tk.Tk()
                root.withdraw()
                messagebox.showerror("Kritischer Fehler", f"Bot konnte nicht gestartet werden:\n{str(e)}")
            except:
                print(f"❌ Kritischer Fehler: {e}")
            
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"❌ Import-Fehler beim Start: {e}")
    sys.exit(1) 