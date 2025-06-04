"""
Einstellungen-Fenster für Bot-Konfiguration
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os


class SettingsWindow:
    def __init__(self, parent):
        self.parent = parent
        self.window = None
        
    def show(self):
        """Zeigt das Einstellungsfenster"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return
            
        self.window = tk.Toplevel(self.parent)
        self.window.title("Bot Einstellungen")
        self.window.geometry("500x400")
        self.window.resizable(False, False)
        
        # Zentriere Fenster
        self.center_window()
        
        # Erstelle GUI-Elemente
        self.create_widgets()
        
    def center_window(self):
        """Zentriert das Fenster auf dem Bildschirm"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        
    def create_widgets(self):
        """Erstellt alle GUI-Elemente"""
        # Hauptframe
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Bot Token Sektion
        token_frame = ttk.LabelFrame(main_frame, text="Bot Token", padding="10")
        token_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(token_frame, text="Discord Bot Token:").pack(anchor=tk.W)
        
        token_entry_frame = ttk.Frame(token_frame)
        token_entry_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.token_var = tk.StringVar()
        self.token_entry = ttk.Entry(token_entry_frame, textvariable=self.token_var, show="*")
        self.token_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Toggle-Button für Token-Anzeige
        self.show_token_var = tk.BooleanVar()
        self.toggle_button = ttk.Checkbutton(
            token_entry_frame, 
            text="Anzeigen",
            variable=self.show_token_var,
            command=self.toggle_token_visibility
        )
        self.toggle_button.pack(side=tk.RIGHT)
        
        # OAuth Sektion
        oauth_frame = ttk.LabelFrame(main_frame, text="OAuth Einstellungen", padding="10")
        oauth_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(oauth_frame, text="Discord Client ID:").pack(anchor=tk.W)
        self.client_id_var = tk.StringVar()
        ttk.Entry(oauth_frame, textvariable=self.client_id_var).pack(fill=tk.X, pady=(5, 10))
        
        ttk.Label(oauth_frame, text="OAuth Port:").pack(anchor=tk.W)
        self.port_var = tk.StringVar(value="5000")
        ttk.Entry(oauth_frame, textvariable=self.port_var).pack(fill=tk.X, pady=(5, 0))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Button(button_frame, text="Speichern", command=self.save_settings).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Abbrechen", command=self.close).pack(side=tk.RIGHT)
        ttk.Button(button_frame, text="Laden", command=self.load_settings).pack(side=tk.LEFT)
        
        # Lade aktuelle Einstellungen
        self.load_settings()
        
    def toggle_token_visibility(self):
        """Ändert die Sichtbarkeit des Bot Tokens"""
        if self.show_token_var.get():
            self.token_entry.config(show="")
        else:
            self.token_entry.config(show="*")
            
    def load_settings(self):
        """Lädt Einstellungen aus .env Datei"""
        try:
            env_path = ".env"
            if os.path.exists(env_path):
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            if '=' in line:
                                key, value = line.split('=', 1)
                                if key == 'DISCORD_BOT_TOKEN':
                                    self.token_var.set(value)
                                elif key == 'DISCORD_CLIENT_ID':
                                    self.client_id_var.set(value)
                                elif key == 'OAUTH_PORT':
                                    self.port_var.set(value)
        except Exception:
            pass
            
    def save_settings(self):
        """Speichert Einstellungen in .env Datei"""
        try:
            settings = {
                'DISCORD_BOT_TOKEN': self.token_var.get().strip(),
                'DISCORD_CLIENT_ID': self.client_id_var.get().strip(),
                'OAUTH_PORT': self.port_var.get().strip()
            }
            
            # Validierung
            if not settings['DISCORD_BOT_TOKEN']:
                messagebox.showerror("Fehler", "Bot Token ist erforderlich!")
                return
                
            # .env Datei schreiben
            with open('.env', 'w', encoding='utf-8') as f:
                f.write("# Sticky-Bot Konfiguration\n")
                for key, value in settings.items():
                    f.write(f"{key}={value}\n")
            
            messagebox.showinfo("Erfolg", "Einstellungen gespeichert!")
            self.close()
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Speichern fehlgeschlagen: {str(e)}")
            
    def close(self):
        """Schließt das Fenster"""
        if self.window:
            self.window.destroy()
            self.window = None 