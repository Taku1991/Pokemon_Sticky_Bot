"""
Sticky Message Manager Dialog
Dialog zum Erstellen neuer Sticky Messages
"""
import tkinter as tk
from tkinter import messagebox, ttk
import os
import json
import logging
from src.utils.permissions import is_bot_editor, is_bot_admin


class StickyManagerDialog:
    def __init__(self, parent, bot):
        self.parent = parent
        self.bot = bot
        self.authenticated_user_id = parent.authenticated_user_id  # User ID des angemeldeten Discord Users
        
        # GUI erstellen
        self.dialog = tk.Toplevel(parent.root)
        self.dialog.title("📝 Neue Sticky Message erstellen")
        self.dialog.geometry("500x600")
        self.dialog.resizable(False, False)
        self.dialog.configure(bg='#2C2F33')
        
        # Dialog zentrieren
        self.dialog.transient(parent.root)
        self.dialog.grab_set()
        
        # Icon setzen
        try:
            self.dialog.iconbitmap('icon.ico')
        except:
            pass
            
        self.setup_gui()
        
    def setup_gui(self):
        # Header
        header_frame = tk.Frame(self.dialog, bg='#5865F2', relief='flat')
        header_frame.pack(fill='x', pady=(0, 20))
        
        title_label = tk.Label(header_frame, 
                              text="📝 Neue Sticky Message", 
                              font=('Segoe UI', 16, 'bold'),
                              fg='white', 
                              bg='#5865F2')
        title_label.pack(pady=15)
        
        # Main Frame
        main_frame = tk.Frame(self.dialog, bg='#2C2F33')
        main_frame.pack(fill='both', expand=True, padx=20)
        
        # Server Auswahl
        server_label = tk.Label(main_frame, text="Server auswählen:", 
                               font=('Segoe UI', 11, 'bold'), fg='#FFFFFF', bg='#2C2F33')
        server_label.pack(anchor='w', pady=(0, 5))
        
        self.server_var = tk.StringVar()
        self.server_combo = ttk.Combobox(main_frame, textvariable=self.server_var, 
                                        state='readonly', font=('Segoe UI', 10))
        self.server_combo.pack(fill='x', pady=(0, 15))
        self.server_combo.bind('<<ComboboxSelected>>', self.on_server_change)
        
        # Channel Auswahl
        channel_label = tk.Label(main_frame, text="Channel auswählen:", 
                                font=('Segoe UI', 11, 'bold'), fg='#FFFFFF', bg='#2C2F33')
        channel_label.pack(anchor='w', pady=(0, 5))
        
        self.channel_var = tk.StringVar()
        self.channel_combo = ttk.Combobox(main_frame, textvariable=self.channel_var, 
                                         state='readonly', font=('Segoe UI', 10))
        self.channel_combo.pack(fill='x', pady=(0, 15))
        
        # Titel
        title_label = tk.Label(main_frame, text="Titel:", 
                              font=('Segoe UI', 11, 'bold'), fg='#FFFFFF', bg='#2C2F33')
        title_label.pack(anchor='w', pady=(0, 5))
        
        self.title_entry = tk.Entry(main_frame, font=('Segoe UI', 10), 
                                   bg='#40444B', fg='#DCDDDE', insertbackground='#FFFFFF')
        self.title_entry.pack(fill='x', ipady=5, pady=(0, 15))
        
        # Nachricht
        message_label = tk.Label(main_frame, text="Nachricht:", 
                                font=('Segoe UI', 11, 'bold'), fg='#FFFFFF', bg='#2C2F33')
        message_label.pack(anchor='w', pady=(0, 5))
        
        self.message_text = tk.Text(main_frame, height=8, font=('Segoe UI', 10),
                                   bg='#40444B', fg='#DCDDDE', insertbackground='#FFFFFF',
                                   wrap=tk.WORD)
        self.message_text.pack(fill='x', pady=(0, 15))
        
        # Verzögerung
        delay_label = tk.Label(main_frame, text="Verzögerung (Sekunden):", 
                              font=('Segoe UI', 11, 'bold'), fg='#FFFFFF', bg='#2C2F33')
        delay_label.pack(anchor='w', pady=(0, 5))
        
        self.delay_entry = tk.Entry(main_frame, font=('Segoe UI', 10), 
                                   bg='#40444B', fg='#DCDDDE', insertbackground='#FFFFFF')
        self.delay_entry.insert(0, "20")
        self.delay_entry.pack(fill='x', ipady=5, pady=(0, 20))
        
        # Buttons
        button_frame = tk.Frame(main_frame, bg='#2C2F33')
        button_frame.pack(fill='x', pady=(0, 20))
        
        cancel_btn = tk.Button(button_frame, text="❌ Abbrechen", 
                              command=self.cancel, font=('Segoe UI', 10, 'bold'),
                              bg='#4F545C', fg='#FFFFFF', relief='flat', cursor='hand2')
        cancel_btn.pack(side='left', ipady=8, ipadx=15)
        
        create_btn = tk.Button(button_frame, text="✅ Erstellen", 
                              command=self.create_sticky, font=('Segoe UI', 10, 'bold'),
                              bg='#00b894', fg='#FFFFFF', relief='flat', cursor='hand2')
        create_btn.pack(side='right', ipady=8, ipadx=15)
        
        # Server und Channel laden
        self.load_servers()
        
    def load_servers(self):
        """Lädt nur Server wo der authentifizierte Discord User Berechtigungen hat"""
        if not self.bot or not hasattr(self.bot, 'guilds'):
            return
            
        if not self.authenticated_user_id:
            # Wenn keine User ID verfügbar, Warnung anzeigen
            self.server_combo['values'] = ["❌ Keine Discord-Anmeldung verfügbar"]
            return
            
        servers = []
        for guild in self.bot.guilds:
            # Prüfe ob authentifizierter User Bot Master oder Editor auf diesem Server ist
            if (is_bot_admin(self.authenticated_user_id, guild.id) or 
                is_bot_editor(self.authenticated_user_id, guild.id)):
                servers.append(f"{guild.name} (ID: {guild.id})")
                
        if not servers:
            # Keine Berechtigungen für Server
            self.server_combo['values'] = ["❌ Du bist auf keinem Server Bot Master/Editor"]
            return
            
        self.server_combo['values'] = servers
        if servers:
            self.server_combo.current(0)
            self.on_server_change()
            
    def on_server_change(self, event=None):
        """Lädt Channels wenn Server geändert wird"""
        if not self.server_var.get():
            return
            
        # Server ID extrahieren
        server_text = self.server_var.get()
        server_id = int(server_text.split("ID: ")[1].rstrip(")"))
        
        # Guild finden
        guild = None
        for g in self.bot.guilds:
            if g.id == server_id:
                guild = g
                break
                
        if not guild:
            return
            
        # Text-Channels laden
        channels = []
        for channel in guild.text_channels:
            channels.append(f"#{channel.name} (ID: {channel.id})")
            
        self.channel_combo['values'] = channels
        if channels:
            self.channel_combo.current(0)
            
    def create_sticky(self):
        """Erstellt eine neue Sticky Message mit Berechtigungsprüfung"""
        try:
            # Zusätzliche Berechtigungsprüfung vor dem Erstellen
            if not self.authenticated_user_id:
                messagebox.showerror("Fehler", "Keine Discord-Anmeldung verfügbar!")
                return
                
            # Server ID extrahieren
            if not self.server_var.get() or "❌" in self.server_var.get():
                messagebox.showerror("Fehler", "Keine gültigen Server verfügbar oder ausgewählt!")
                return
                
            server_text = self.server_var.get()
            server_id = int(server_text.split("ID: ")[1].rstrip(")"))
            
            # Finale Berechtigungsprüfung mit authentifizierter User ID
            if not (is_bot_admin(self.authenticated_user_id, server_id) or 
                    is_bot_editor(self.authenticated_user_id, server_id)):
                messagebox.showerror("Sicherheitsfehler", 
                                   f"Du hast keine Berechtigung für Server '{server_text.split(' (ID:')[0]}'!")
                return
            
            # Validierung
            if not self.channel_var.get():
                messagebox.showerror("Fehler", "Bitte wähle einen Channel aus!")
                return
                
            if not self.title_entry.get().strip():
                messagebox.showerror("Fehler", "Bitte gib einen Titel ein!")
                return
                
            if not self.message_text.get("1.0", tk.END).strip():
                messagebox.showerror("Fehler", "Bitte gib eine Nachricht ein!")
                return
                
            try:
                delay = int(self.delay_entry.get())
                if delay < 5:
                    messagebox.showerror("Fehler", "Verzögerung muss mindestens 5 Sekunden sein!")
                    return
            except ValueError:
                messagebox.showerror("Fehler", "Bitte gib eine gültige Zahl für die Verzögerung ein!")
                return
                
            # Channel ID extrahieren
            channel_text = self.channel_var.get()
            channel_id = channel_text.split("ID: ")[1].rstrip(")")
            
            # Channel Name extrahieren
            channel_name = channel_text.split(" (ID:")[0].lstrip("#")
            
            # Sticky Message Daten
            sticky_data = {
                "title": self.title_entry.get().strip(),
                "message": self.message_text.get("1.0", tk.END).strip(),
                "delay": delay,
                "channel_name": channel_name,
                "example": None,
                "footer": None
            }
            
            # In Datei speichern
            self.save_sticky_message(channel_id, sticky_data)
            
            messagebox.showinfo("Erfolg", f"Sticky Message für #{channel_name} wurde erstellt!")
            
            # Parent-Fenster aktualisieren
            if hasattr(self.parent, 'refresh_sticky_list'):
                self.parent.refresh_sticky_list()
                
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Erstellen: {str(e)}")
            logging.error(f"Fehler beim Erstellen der Sticky Message: {e}")
            
    def save_sticky_message(self, channel_id, sticky_data):
        """Speichert Sticky Message verschlüsselt - SICHERHEIT!"""
        try:
            # Verwende das verschlüsselte System
            from src.utils.secure_storage import load_sticky_messages_secure, save_sticky_messages_secure
            
            # Bot Token versuchen zu bekommen
            bot_token = None
            try:
                if self.bot and hasattr(self.bot, 'http') and hasattr(self.bot.http, 'token'):
                    bot_token = self.bot.http.token
            except:
                pass
            
            # Bestehende Daten laden (verschlüsselt)
            sticky_messages = load_sticky_messages_secure(bot_token)
            
            # Neue Daten hinzufügen
            sticky_messages[channel_id] = sticky_data
            
            # Verschlüsselt speichern
            save_sticky_messages_secure(sticky_messages, bot_token)
            
            logging.info(f"🔐 Sticky Message für Channel {channel_id} sicher gespeichert")
            
        except Exception as e:
            logging.error(f"❌ Fehler beim sicheren Speichern der Sticky Message: {e}")
            raise
            
    def cancel(self):
        """Schließt den Dialog"""
        self.dialog.destroy() 