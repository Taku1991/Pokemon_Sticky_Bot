import discord
from discord.ext import commands
import asyncio
import logging
import os
import sys
import traceback
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk, simpledialog
import threading
from datetime import datetime
from PIL import Image, ImageTk
import json
from src.utils.permissions import is_bot_editor, is_bot_admin

# Debug-Logging für .exe
def setup_debug_logging():
    """Setup Debug-Logging für .exe Probleme"""
    try:
        # Bestimme den korrekten Pfad für Log-Datei
        if getattr(sys, 'frozen', False):
            # Bei .exe: Neben der .exe Datei
            app_path = os.path.dirname(sys.executable)
        else:
            # Bei Python-Skript: Im Projektordner
            app_path = os.path.dirname(os.path.abspath(__file__))
            
        log_file = os.path.join(app_path, 'sticky_bot_debug.log')
        
        # Prüfe ob wir in GUI-Mode sind (keine Console)
        has_console = True
        try:
            # Test ob Console verfügbar ist
            sys.stdout.write('')
            sys.stdout.flush()
        except:
            has_console = False
        
        # Windows Console Encoding Fix (nur wenn Console verfügbar)
        if has_console and sys.platform.startswith('win'):
            try:
                import codecs
                sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
                sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())
            except:
                pass  # Fallback wenn das nicht funktioniert
        
        # Logging Handler Setup
        handlers = [logging.FileHandler(log_file, encoding='utf-8')]
        
        # Console Handler nur wenn verfügbar
        if has_console:
            handlers.append(logging.StreamHandler(sys.stdout))
        
        logging.basicConfig(
            level=logging.DEBUG,
            format='[%(asctime)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=handlers
        )
        
        logging.info("=== STICKY-BOT DEBUG START ===")
        logging.info(f"Python Version: {sys.version}")
        logging.info(f"Working Directory: {os.getcwd()}")
        logging.info(f"Executable: {sys.executable}")
        logging.info(f"Frozen: {getattr(sys, 'frozen', False)}")
        logging.info(f"Console Available: {has_console}")
        logging.info(f"App Path: {app_path}")
        
    except Exception as e:
        # Fallback - versuche wenigstens Datei-Logging
        try:
            with open(os.path.join(app_path, 'error.log'), 'w') as f:
                f.write(f"Debug-Logging Setup fehlgeschlagen: {e}\n")
        except:
            pass

# Früh starten
setup_debug_logging()

# Globale Variable für das Status-Fenster
status_window = None
bot_thread = None
bot_running = False

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
        """Speichert Sticky Message in JSON-Datei"""
        try:
            # Pfad zur Sticky Messages Datei
            data_dir = os.path.join(APP_PATH, 'data')
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
                
            sticky_file = os.path.join(data_dir, 'sticky_messages.json')
            
            # Bestehende Daten laden
            sticky_messages = {}
            if os.path.exists(sticky_file):
                with open(sticky_file, 'r', encoding='utf-8') as f:
                    sticky_messages = json.load(f)
                    
            # Neue Daten hinzufügen
            sticky_messages[channel_id] = sticky_data
            
            # Speichern
            with open(sticky_file, 'w', encoding='utf-8') as f:
                json.dump(sticky_messages, f, indent=2, ensure_ascii=False)
                
            logging.info(f"Sticky Message für Channel {channel_id} gespeichert")
            
        except Exception as e:
            logging.error(f"Fehler beim Speichern der Sticky Message: {e}")
            raise
            
    def cancel(self):
        """Schließt den Dialog"""
        self.dialog.destroy()

class BotStatusWindow:
    def __init__(self):
        self.authenticated_user = None
        self.authenticated_user_id = None
        
        # GUI erst erstellen
        self.root = tk.Tk()
        self.root.title("🤖 Sticky-Bot - Kontrollzentrum")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # Icon versuchen zu setzen
        try:
            self.root.iconbitmap('icon.ico')
        except:
            pass
        
        # Modernes Theme
        self.root.configure(bg='#2C2F33')
        
        # Zentrieren
        self.root.eval('tk::PlaceWindow . center')
        
        # Hintergrundbild laden
        self.background_image = None
        self.load_background()
        
        self.setup_gui()
        
        # Nach GUI-Setup: Discord Login durchführen
        # self.root.after(100, self.authenticate_user_async)  # Entfernt - Authentifizierung erst beim Bot-Start
        
        # Beim Schließen des Fensters den Bot beenden
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def authenticate_user_async(self):
        """Authentifizierung nach GUI-Setup"""
        # Authentifizierung in separatem Thread
        def auth_thread():
            success = self.authenticate_user()
            # Zurück zum GUI-Thread
            self.root.after(0, lambda: self.handle_auth_result(success))
        
        import threading
        thread = threading.Thread(target=auth_thread, daemon=True)
        thread.start()
        
    def handle_auth_result(self, success):
        """Behandelt das Ergebnis der Authentifizierung"""
        if not success:
            print("❌ Discord Verification abgebrochen oder fehlgeschlagen")
            self.root.destroy()
            sys.exit(1)
        else:
            print("✅ Discord Verification erfolgreich!")
        
    def load_background(self):
        """Lädt das Hintergrundbild"""
        try:
            # Versuche verschiedene Bildpfade
            image_paths = [
                'StickyBot.png',
                'icon.png', 
                'background.png',
                'pikachu.png'
            ]
            
            for path in image_paths:
                if os.path.exists(path):
                    # Bild laden und skalieren
                    pil_image = Image.open(path)
                    # Bild auf passende Größe skalieren (aber nicht zu groß)
                    pil_image = pil_image.resize((150, 150), Image.Resampling.LANCZOS)
                    # Transparenz hinzufügen
                    pil_image = pil_image.convert("RGBA")
                    # Bild etwas transparenter machen
                    alpha = pil_image.split()[3]
                    alpha = alpha.point(lambda p: int(p * 0.3))  # 30% Transparenz
                    pil_image.putalpha(alpha)
                    
                    self.background_image = ImageTk.PhotoImage(pil_image)
                    logging.info(f"✅ Hintergrundbild geladen: {path}")
                    break
        except Exception as e:
            logging.warning(f"⚠️ Hintergrundbild konnte nicht geladen werden: {e}")
            self.background_image = None
        
    def setup_gui(self):
        # Benutzerdefinierte Tab-Buttons anstelle von Notebook
        self.tab_frame = tk.Frame(self.root, bg='#2C2F33')
        self.tab_frame.pack(fill='x', padx=10, pady=(10, 0))
        
        # Tab Buttons - Etwas kleiner aber immer noch gut klickbar
        self.status_tab_btn = tk.Button(self.tab_frame,
                                       text="📊 Bot Status",
                                       command=lambda: self.switch_tab('status'),
                                       font=('Segoe UI', 12, 'bold'),
                                       bg='#5865F2',
                                       fg='#FFFFFF',
                                       activebackground='#4752C4',
                                       activeforeground='#FFFFFF',
                                       relief='flat',
                                       bd=0,
                                       cursor='hand2',
                                       height=1)
        self.status_tab_btn.pack(side='left', fill='x', expand=True, ipady=8, padx=(0, 2))
        
        self.sticky_tab_btn = tk.Button(self.tab_frame,
                                       text="📝 Sticky Manager",
                                       command=lambda: self.switch_tab('sticky'),
                                       font=('Segoe UI', 12, 'bold'),
                                       bg='#36393F',
                                       fg='#B9BBBE',
                                       activebackground='#40444B',
                                       activeforeground='#FFFFFF',
                                       relief='flat',
                                       bd=0,
                                       cursor='hand2',
                                       height=1)
        self.sticky_tab_btn.pack(side='left', fill='x', expand=True, ipady=8, padx=(2, 2))
        
        self.server_tab_btn = tk.Button(self.tab_frame,
                                       text="🏠 Server Verwaltung",
                                       command=lambda: self.switch_tab('server'),
                                       font=('Segoe UI', 12, 'bold'),
                                       bg='#36393F',
                                       fg='#B9BBBE',
                                       activebackground='#40444B',
                                       activeforeground='#FFFFFF',
                                       relief='flat',
                                       bd=0,
                                       cursor='hand2',
                                       height=1)
        self.server_tab_btn.pack(side='right', fill='x', expand=True, ipady=8, padx=(2, 0))
        
        # Content Frame für die Tab-Inhalte
        self.content_frame = tk.Frame(self.root, bg='#2C2F33')
        self.content_frame.pack(fill='both', expand=True, padx=10, pady=(5, 10))
        
        # Tab Frames erstellen
        self.status_frame = tk.Frame(self.content_frame, bg='#2C2F33')
        self.sticky_frame = tk.Frame(self.content_frame, bg='#2C2F33')
        self.server_frame = tk.Frame(self.content_frame, bg='#2C2F33')
        
        # Setup aller Tabs
        self.setup_status_tab()
        self.setup_sticky_tab()
        self.setup_server_tab()
        
        # Standard: Status Tab aktiv
        self.current_tab = 'status'
        self.switch_tab('status')
        
    def switch_tab(self, tab_name):
        """Wechselt zwischen den Tabs"""
        
        # Spezielle Behandlung für Sticky Manager - Authentifizierung erforderlich
        if tab_name == 'sticky':
            if not self.authenticated_user_id:
                # ECHTES Challenge-Response System
                success = self.authenticate_user()
                if not success:
                    # Authentifizierung fehlgeschlagen - bleibe beim aktuellen Tab
                    return
        
        self.current_tab = tab_name
        
        # Alle Frames verstecken
        self.status_frame.pack_forget()
        self.sticky_frame.pack_forget()
        self.server_frame.pack_forget()
        
        # Alle Buttons auf inaktiv setzen
        self.status_tab_btn.config(bg='#36393F', fg='#B9BBBE', activebackground='#40444B')
        self.sticky_tab_btn.config(bg='#36393F', fg='#B9BBBE', activebackground='#40444B')
        self.server_tab_btn.config(bg='#36393F', fg='#B9BBBE', activebackground='#40444B')
        
        if tab_name == 'status':
            # Status Tab aktivieren
            self.status_frame.pack(fill='both', expand=True)
            self.status_tab_btn.config(bg='#5865F2', fg='#FFFFFF', activebackground='#4752C4')
            
        elif tab_name == 'sticky':
            # Sticky Tab aktivieren
            self.sticky_frame.pack(fill='both', expand=True)
            self.sticky_tab_btn.config(bg='#00b894', fg='#FFFFFF', activebackground='#00a085')
            # Sticky Liste aktualisieren wenn Tab geöffnet wird
            self.refresh_sticky_list()
            
        elif tab_name == 'server':
            # Server Tab aktivieren
            self.server_frame.pack(fill='both', expand=True)
            self.server_tab_btn.config(bg='#FAA61A', fg='#2C2F33', activebackground='#E89C0D')
            # Server Liste aktualisieren wenn Tab geöffnet wird
            self.refresh_server_list()
        
    def setup_status_tab(self):
        """Setup des Bot Status Tabs"""
        # Canvas für Hintergrundbild
        self.canvas = tk.Canvas(self.status_frame, bg='#2C2F33', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        
        # Hintergrundbild hinzufügen (falls verfügbar)
        if self.background_image:
            self.canvas.create_image(700, 600, image=self.background_image, anchor='se')
        
        # Main Frame über dem Canvas
        main_frame = tk.Frame(self.canvas, bg='#2C2F33')
        self.canvas.create_window(0, 0, window=main_frame, anchor='nw')
        
        # Header
        header_frame = tk.Frame(main_frame, bg='#5865F2', relief='flat')
        header_frame.pack(fill='x', pady=(0, 10), padx=10)
        
        title_label = tk.Label(header_frame, 
                              text="🤖 Sticky-Bot Kontrollzentrum", 
                              font=('Segoe UI', 18, 'bold'),
                              fg='white', 
                              bg='#5865F2')
        title_label.pack(pady=15)
        
        # Status Info Frame
        info_frame = tk.Frame(main_frame, bg='#36393F', relief='flat')
        info_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        info_inner = tk.Frame(info_frame, bg='#36393F')
        info_inner.pack(padx=15, pady=10)
        
        # Bot Status
        self.status_label = tk.Label(info_inner,
                                    text="⏸️ Bot gestoppt",
                                    font=('Segoe UI', 14, 'bold'),
                                    fg='#ed4245',
                                    bg='#36393F')
        self.status_label.pack(anchor='w')
        
        # Bot Info
        self.info_label = tk.Label(info_inner,
                                  text="Bereit zum Starten...",
                                  font=('Segoe UI', 11),
                                  fg='#B9BBBE',
                                  bg='#36393F')
        self.info_label.pack(anchor='w', pady=(5, 0))
        
        # Control Buttons Frame
        control_frame = tk.Frame(main_frame, bg='#2C2F33')
        control_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        # Start Button
        self.start_btn = tk.Button(control_frame,
                                  text="▶️ BOT STARTEN",
                                  command=self.start_bot,
                                  font=('Segoe UI', 14, 'bold'),
                                  bg='#00b894',
                                  fg='#FFFFFF',
                                  activebackground='#00a085',
                                  activeforeground='#FFFFFF',
                                  relief='flat',
                                  bd=0,
                                  cursor='hand2',
                                  height=2)
        self.start_btn.pack(side='left', fill='x', expand=True, ipady=10, padx=(0, 5))
        
        # Stop Button
        self.stop_btn = tk.Button(control_frame,
                                 text="⏹️ BOT STOPPEN",
                                 command=self.stop_bot,
                                 font=('Segoe UI', 14, 'bold'),
                                 bg='#ed4245',
                                 fg='#FFFFFF',
                                 activebackground='#c73e41',
                                 activeforeground='#FFFFFF',
                                 relief='flat',
                                 bd=0,
                                 cursor='hand2',
                                 height=2,
                                 state='disabled')
        self.stop_btn.pack(side='right', fill='x', expand=True, ipady=10, padx=(5, 0))
        
        # Log Bereich
        log_frame = tk.Frame(main_frame, bg='#2C2F33')
        log_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        log_label = tk.Label(log_frame,
                            text="📋 Bot-Log:",
                            font=('Segoe UI', 12, 'bold'),
                            fg='#FFFFFF',
                            bg='#2C2F33')
        log_label.pack(anchor='w', pady=(0, 5))
        
        # Scrollbares Text-Widget für Logs
        self.log_text = scrolledtext.ScrolledText(log_frame,
                                                 font=('Consolas', 9),
                                                 bg='#40444B',
                                                 fg='#DCDDDE',
                                                 insertbackground='#FFFFFF',
                                                 relief='flat',
                                                 wrap=tk.WORD,
                                                 height=10)
        self.log_text.pack(fill='both', expand=True)
        
        # Button Frame für zusätzliche Funktionen
        button_frame = tk.Frame(main_frame, bg='#2C2F33')
        button_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        # Restart Button
        self.restart_btn = tk.Button(button_frame,
                                    text="🔄 Neu starten",
                                    command=self.restart_bot,
                                    font=('Segoe UI', 10, 'bold'),
                                    bg='#FAA61A',
                                    fg='#2C2F33',
                                    activebackground='#E89C0D',
                                    activeforeground='#2C2F33',
                                    relief='flat',
                                    bd=0,
                                    cursor='hand2')
        self.restart_btn.pack(side='left', ipady=8, ipadx=15)
        
        # Token Setup Button
        self.token_btn = tk.Button(button_frame,
                                  text="🔑 Token ändern",
                                  command=self.change_token,
                                  font=('Segoe UI', 10, 'bold'),
                                  bg='#5865F2',
                                  fg='#FFFFFF',
                                  activebackground='#4752C4',
                                  activeforeground='#FFFFFF',
                                  relief='flat',
                                  bd=0,
                                  cursor='hand2')
        self.token_btn.pack(side='left', padx=(10, 0), ipady=8, ipadx=15)
        
        # Beenden Button
        self.quit_btn = tk.Button(button_frame,
                                 text="❌ Programm beenden",
                                 command=self.on_closing,
                                 font=('Segoe UI', 10, 'bold'),
                                 bg='#4F545C',
                                 fg='#FFFFFF',
                                 activebackground='#5D6269',
                                 activeforeground='#FFFFFF',
                                 relief='flat',
                                 bd=0,
                                 cursor='hand2')
        self.quit_btn.pack(side='right', ipady=8, ipadx=15)
        
        # Frame-Größe an Canvas anpassen
        main_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
        # Canvas-Größe an Fenster anpassen
        def configure_canvas(event):
            try:
                canvas_width = event.width
                canvas_items = self.canvas.find_all()
                if canvas_items:
                    # Nur das main_frame skalieren, nicht das Hintergrundbild
                    main_frame_item = canvas_items[0] if len(canvas_items) > 0 else None
                    if main_frame_item:
                        # Prüfe ob das Element eine 'width' Option unterstützt
                        try:
                            self.canvas.itemconfig(main_frame_item, width=canvas_width)
                        except tk.TclError:
                            # Element unterstützt keine 'width' Option - das ist ok
                            pass
            except Exception as e:
                # Fehler beim Canvas-Resize ignorieren
                pass
        
        self.canvas.bind('<Configure>', configure_canvas)
        
    def setup_sticky_tab(self):
        """Setup des Sticky Manager Tabs"""
        # Header
        header_frame = tk.Frame(self.sticky_frame, bg='#5865F2', relief='flat')
        header_frame.pack(fill='x', pady=(0, 15), padx=10)
        
        title_label = tk.Label(header_frame, 
                              text="📝 Sticky Messages Verwaltung", 
                              font=('Segoe UI', 16, 'bold'),
                              fg='white', 
                              bg='#5865F2')
        title_label.pack(pady=12)
        
        # Control Buttons
        control_frame = tk.Frame(self.sticky_frame, bg='#2C2F33')
        control_frame.pack(fill='x', padx=10, pady=(0, 15))
        
        # Neue Sticky Message Button
        self.new_sticky_btn = tk.Button(control_frame,
                                       text="➕ Neue Sticky Message",
                                       command=self.create_new_sticky,
                                       font=('Segoe UI', 11, 'bold'),
                                       bg='#00b894',
                                       fg='#FFFFFF',
                                       activebackground='#00a085',
                                       activeforeground='#FFFFFF',
                                       relief='flat',
                                       bd=0,
                                       cursor='hand2')
        self.new_sticky_btn.pack(side='left', ipady=8, ipadx=20)
        
        # Refresh Button
        self.refresh_btn = tk.Button(control_frame,
                                    text="🔄 Aktualisieren",
                                    command=self.refresh_sticky_list,
                                    font=('Segoe UI', 11, 'bold'),
                                    bg='#5865F2',
                                    fg='#FFFFFF',
                                    activebackground='#4752C4',
                                    activeforeground='#FFFFFF',
                                    relief='flat',
                                    bd=0,
                                    cursor='hand2')
        self.refresh_btn.pack(side='left', padx=(10, 0), ipady=8, ipadx=20)
        
        # Sticky Messages Liste
        list_frame = tk.Frame(self.sticky_frame, bg='#36393F', relief='flat')
        list_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Liste Header
        list_header = tk.Label(list_frame,
                              text="📋 Aktive Sticky Messages:",
                              font=('Segoe UI', 12, 'bold'),
                              fg='#FFFFFF',
                              bg='#36393F')
        list_header.pack(anchor='w', padx=15, pady=(15, 10))
        
        # Scrollable Frame für die Liste
        self.sticky_list_frame = tk.Frame(list_frame, bg='#36393F')
        self.sticky_list_frame.pack(fill='both', expand=True, padx=15, pady=(0, 15))
        
        # Initial laden
        self.refresh_sticky_list()
        
    def create_new_sticky(self):
        """Öffnet Dialog für neue Sticky Message"""
        if not bot_running or not bot:
            messagebox.showwarning("Bot nicht verfügbar", 
                                 "Der Bot muss gestartet sein, um Sticky Messages zu erstellen!")
            return
            
        dialog = StickyManagerDialog(self, bot)
        
    def refresh_sticky_list(self):
        """Aktualisiert die Liste der Sticky Messages - nur berechtigte anzeigen"""
        # Authentifizierte User ID verwenden
        authenticated_user_id = self.authenticated_user_id
        
        # Alte Widgets entfernen
        for widget in self.sticky_list_frame.winfo_children():
            widget.destroy()
            
        try:
            # Sticky Messages laden
            data_dir = os.path.join(APP_PATH, 'data')
            sticky_file = os.path.join(data_dir, 'sticky_messages.json')
            
            sticky_messages = {}
            if os.path.exists(sticky_file):
                with open(sticky_file, 'r', encoding='utf-8') as f:
                    sticky_messages = json.load(f)
                    
            # Nur berechtigte Sticky Messages anzeigen
            authorized_stickies = {}
            if authenticated_user_id and bot and bot_running:
                for channel_id, data in sticky_messages.items():
                    try:
                        channel = bot.get_channel(int(channel_id))
                        if channel and (is_bot_admin(authenticated_user_id, channel.guild.id) or 
                                       is_bot_editor(authenticated_user_id, channel.guild.id)):
                            authorized_stickies[channel_id] = data
                    except:
                        # Falls Channel nicht gefunden wird, zeige trotzdem an wenn User Admin ist
                        # (für den Fall dass Bot temporär nicht auf dem Server ist)
                        pass
            
            if not authorized_stickies:
                # Keine berechtigten Sticky Messages vorhanden
                if not authenticated_user_id:
                    message = "🔐 Keine Discord-Anmeldung\n\nBitte melde dich mit Discord an und stelle sicher, dass du Bot Master auf mindestens einem Server bist!"
                elif not sticky_messages:
                    message = "📭 Keine Sticky Messages vorhanden\n\nKlicke auf '➕ Neue Sticky Message' um eine zu erstellen!"
                else:
                    message = "🔒 Keine berechtigten Sticky Messages\n\nDu kannst nur Sticky Messages von Servern verwalten, wo du Bot Master oder Editor bist!"
                    
                no_sticky_label = tk.Label(self.sticky_list_frame,
                                          text=message,
                                          font=('Segoe UI', 11),
                                          fg='#B9BBBE',
                                          bg='#36393F',
                                          justify='center')
                no_sticky_label.pack(expand=True)
                return
                
            # Berechtigte Sticky Messages anzeigen
            for channel_id, data in authorized_stickies.items():
                self.create_sticky_item(channel_id, data)
                
        except Exception as e:
            error_label = tk.Label(self.sticky_list_frame,
                                  text=f"❌ Fehler beim Laden: {str(e)}",
                                  font=('Segoe UI', 11),
                                  fg='#ed4245',
                                  bg='#36393F')
            error_label.pack(expand=True)
            logging.error(f"Fehler beim Laden der Sticky Messages: {e}")
            
    def create_sticky_item(self, channel_id, data):
        """Erstellt ein Widget für eine Sticky Message"""
        # Container für diese Sticky Message
        item_frame = tk.Frame(self.sticky_list_frame, bg='#40444B', relief='flat', bd=1)
        item_frame.pack(fill='x', pady=5)
        
        # Hauptinhalt
        content_frame = tk.Frame(item_frame, bg='#40444B')
        content_frame.pack(fill='x', padx=15, pady=10)
        
        # Server und Channel Info
        channel_info = f"#{data.get('channel_name', 'Unbekannt')}"
        if bot and bot_running:
            # Versuche Server-Name zu finden
            try:
                channel = bot.get_channel(int(channel_id))
                if channel:
                    channel_info = f"{channel.guild.name} → #{channel.name}"
            except:
                pass
                
        info_label = tk.Label(content_frame,
                             text=channel_info,
                             font=('Segoe UI', 11, 'bold'),
                             fg='#FFFFFF',
                             bg='#40444B')
        info_label.pack(anchor='w')
        
        # Titel und Details
        title_text = data.get('title', 'Kein Titel')[:50]
        if len(data.get('title', '')) > 50:
            title_text += "..."
            
        details_text = f"Titel: {title_text}\nVerzögerung: {data.get('delay', 20)} Sekunden"
        
        details_label = tk.Label(content_frame,
                                text=details_text,
                                font=('Segoe UI', 9),
                                fg='#B9BBBE',
                                bg='#40444B',
                                justify='left')
        details_label.pack(anchor='w', pady=(5, 0))
        
        # Button Frame
        button_frame = tk.Frame(content_frame, bg='#40444B')
        button_frame.pack(fill='x', pady=(10, 0))
        
        # Status (aktiv/inaktiv) - für zukünftige Implementierung
        status_label = tk.Label(button_frame,
                               text="✅ Aktiv",
                               font=('Segoe UI', 9, 'bold'),
                               fg='#00b894',
                               bg='#40444B')
        status_label.pack(side='left')
        
        # Löschen Button
        delete_btn = tk.Button(button_frame,
                              text="🗑️ Löschen",
                              command=lambda cid=channel_id: self.delete_sticky(cid),
                              font=('Segoe UI', 9, 'bold'),
                              bg='#ed4245',
                              fg='#FFFFFF',
                              activebackground='#c73e41',
                              activeforeground='#FFFFFF',
                              relief='flat',
                              bd=0,
                              cursor='hand2')
        delete_btn.pack(side='right', ipady=4, ipadx=10)
        
    def delete_sticky(self, channel_id):
        """Löscht eine Sticky Message mit Berechtigungsprüfung"""
        try:
            # Berechtigungsprüfung mit authentifizierter User ID
            if not self.authenticated_user_id:
                messagebox.showerror("Sicherheitsfehler", "Keine Discord-Anmeldung verfügbar!")
                return
                
            # Prüfe Berechtigung für den spezifischen Channel/Server
            authorized = False
            if bot and bot_running:
                try:
                    channel = bot.get_channel(int(channel_id))
                    if channel and (is_bot_admin(self.authenticated_user_id, channel.guild.id) or 
                                   is_bot_editor(self.authenticated_user_id, channel.guild.id)):
                        authorized = True
                except:
                    pass
                    
            if not authorized:
                messagebox.showerror("Sicherheitsfehler", 
                                   "Du hast keine Berechtigung, diese Sticky Message zu löschen!")
                return
            
            # Bestätigung
            result = messagebox.askyesno("Sticky Message löschen?", 
                                       "Möchtest du diese Sticky Message wirklich löschen?")
            if not result:
                return
                
            # Aus Datei entfernen
            data_dir = os.path.join(APP_PATH, 'data')
            sticky_file = os.path.join(data_dir, 'sticky_messages.json')
            
            sticky_messages = {}
            if os.path.exists(sticky_file):
                with open(sticky_file, 'r', encoding='utf-8') as f:
                    sticky_messages = json.load(f)
                    
            if channel_id in sticky_messages:
                del sticky_messages[channel_id]
                
                # Speichern
                with open(sticky_file, 'w', encoding='utf-8') as f:
                    json.dump(sticky_messages, f, indent=2, ensure_ascii=False)
                    
                self.add_log(f"🗑️ Sticky Message für Channel {channel_id} gelöscht")
                messagebox.showinfo("Erfolg", "Sticky Message wurde gelöscht!")
                
                # Liste aktualisieren
                self.refresh_sticky_list()
            else:
                messagebox.showwarning("Nicht gefunden", "Sticky Message wurde nicht gefunden!")
                
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Löschen: {str(e)}")
            logging.error(f"Fehler beim Löschen der Sticky Message: {e}")

    def start_bot(self):
        """Startet den Bot"""
        global bot_running, bot_thread
        
        if bot_running:
            self.add_log("⚠️ Bot läuft bereits!")
            return
            
        # Bot starten ohne Authentifizierung
        self.add_log("▶️ Bot wird gestartet...")
        self.update_status("🔄 Bot startet...", "Verbindung wird aufgebaut...", "#FAA61A")
        
        # Buttons aktualisieren
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        
        # Bot in separatem Thread starten
        bot_thread = start_bot_thread()
        bot_running = True
        
    def stop_bot(self):
        """Stoppt den Bot"""
        global bot_running, bot
        
        if not bot_running:
            self.add_log("⚠️ Bot läuft nicht!")
            return
            
        self.add_log("⏹️ Bot wird gestoppt...")
        self.update_status("⏹️ Bot wird gestoppt...", "Verbindungen werden getrennt...", "#FAA61A")
        
        try:
            # Bot sauber beenden
            if bot and not bot.is_closed():
                asyncio.run_coroutine_threadsafe(bot.close(), bot.loop)
            
            bot_running = False
            
            # Buttons aktualisieren
            self.start_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
            
            self.update_status("⏸️ Bot gestoppt", "Bereit zum Starten...", "#ed4245")
            self.add_log("✅ Bot erfolgreich gestoppt")
            
        except Exception as e:
            self.add_log(f"❌ Fehler beim Stoppen: {e}")
            logging.error(f"Fehler beim Bot-Stop: {e}")
        
    def add_log(self, message):
        """Fügt eine Log-Nachricht hinzu"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        # Im GUI-Thread ausführen
        self.root.after(0, self._add_log_safe, formatted_message)
        
    def _add_log_safe(self, message):
        """Thread-sichere Log-Hinzufügung"""
        try:
            self.log_text.insert(tk.END, message)
            self.log_text.see(tk.END)  # Automatisch nach unten scrollen
            
            # Begrenze die Anzahl der Zeilen (letzte 1000 behalten)
            lines = self.log_text.get("1.0", tk.END).split('\n')
            if len(lines) > 1000:
                self.log_text.delete("1.0", f"{len(lines)-1000}.0")
        except:
            pass  # Ignoriere Fehler wenn Fenster geschlossen wird
            
    def update_status(self, status, info="", color="#FAA61A"):
        """Aktualisiert den Bot-Status"""
        self.root.after(0, self._update_status_safe, status, info, color)
        
    def _update_status_safe(self, status, info, color):
        """Thread-sichere Status-Aktualisierung"""
        try:
            self.status_label.config(text=status, fg=color)
            self.info_label.config(text=info)
        except:
            pass
            
    def restart_bot(self):
        """Startet den Bot neu"""
        result = messagebox.askyesno("🔄 Bot neu starten?", 
                                   "Möchtest du den Bot wirklich neu starten?\n"
                                   "Alle aktiven Verbindungen werden getrennt.")
        if result:
            self.add_log("🔄 Bot wird neu gestartet...")
            # Bot neu starten
            if getattr(sys, 'frozen', False):
                os.execv(sys.executable, sys.argv)
            else:
                os.execv(sys.executable, [sys.executable] + sys.argv)
                
    def change_token(self):
        """Öffnet das Token-Setup"""
        result = messagebox.askyesno("🔑 Token ändern?", 
                                   "Möchtest du einen neuen Discord Bot Token eingeben?\n"
                                   "Der Bot wird danach neu gestartet.")
        if result:
            # .env löschen um Setup zu erzwingen
            env_path = os.path.join(APP_PATH, '.env')
            if os.path.exists(env_path):
                os.remove(env_path)
                self.add_log("🗑️ Alter Token gelöscht")
            
            self.add_log("🔑 Token-Setup wird gestartet...")
            # Bot neu starten für Token-Setup
            if getattr(sys, 'frozen', False):
                os.execv(sys.executable, sys.argv)
            else:
                os.execv(sys.executable, [sys.executable] + sys.argv)
                
    def on_closing(self):
        """Wird beim Schließen des Fensters aufgerufen"""
        result = messagebox.askyesno("🤔 Programm beenden?", 
                                   "Möchtest du den Sticky-Bot wirklich beenden?\n"
                                   "Alle Sticky Messages werden gestoppt.")
        if result:
            self.add_log("👋 Programm wird beendet...")
            
            # Bot stoppen falls er läuft
            if bot_running:
                self.stop_bot()
            
            self.root.after(100, self._force_quit)  # Kurz warten, dann beenden
            
    def _force_quit(self):
        """Beendet das Programm"""
        try:
            self.root.quit()
            self.root.destroy()
        except:
            pass
        finally:
            os._exit(0)  # Erzwinge das Beenden
            
    def run(self):
        """Startet das Status-Fenster"""
        self.root.mainloop()

    def setup_server_tab(self):
        """Setup des Server Verwaltungs Tabs"""
        # Header
        header_frame = tk.Frame(self.server_frame, bg='#FAA61A', relief='flat')
        header_frame.pack(fill='x', pady=(0, 15), padx=10)
        
        title_label = tk.Label(header_frame, 
                              text="🏠 Server & Berechtigungen Verwaltung", 
                              font=('Segoe UI', 16, 'bold'),
                              fg='#2C2F33', 
                              bg='#FAA61A')
        title_label.pack(pady=12)
        
        # Main Container mit zwei Spalten
        main_container = tk.Frame(self.server_frame, bg='#2C2F33')
        main_container.pack(fill='both', expand=True, padx=10)
        
        # Linke Spalte: Server Liste
        left_frame = tk.Frame(main_container, bg='#36393F', relief='flat')
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        # Server Liste Header
        server_header = tk.Label(left_frame,
                                text="🌐 Verbundene Server:",
                                font=('Segoe UI', 12, 'bold'),
                                fg='#FFFFFF',
                                bg='#36393F')
        server_header.pack(anchor='w', padx=15, pady=(15, 10))
        
        # Server Liste Container
        self.server_list_frame = tk.Frame(left_frame, bg='#36393F')
        self.server_list_frame.pack(fill='both', expand=True, padx=15, pady=(0, 15))
        
        # Rechte Spalte: Bot Master Verwaltung
        right_frame = tk.Frame(main_container, bg='#36393F', relief='flat')
        right_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))
        
        # Bot Master Header
        master_header = tk.Label(right_frame,
                                text="👑 Bot Master & Editoren:",
                                font=('Segoe UI', 12, 'bold'),
                                fg='#FFFFFF',
                                bg='#36393F')
        master_header.pack(anchor='w', padx=15, pady=(15, 10))
        
        # Bot Master Liste Container
        self.master_list_frame = tk.Frame(right_frame, bg='#36393F')
        self.master_list_frame.pack(fill='both', expand=True, padx=15, pady=(0, 15))
        
        # Control Buttons für Bot Master
        master_control_frame = tk.Frame(right_frame, bg='#36393F')
        master_control_frame.pack(fill='x', padx=15, pady=(0, 15))
        
        # Refresh Button
        refresh_master_btn = tk.Button(master_control_frame,
                                      text="🔄 Aktualisieren",
                                      command=self.refresh_server_list,
                                      font=('Segoe UI', 10, 'bold'),
                                      bg='#5865F2',
                                      fg='#FFFFFF',
                                      activebackground='#4752C4',
                                      activeforeground='#FFFFFF',
                                      relief='flat',
                                      bd=0,
                                      cursor='hand2')
        refresh_master_btn.pack(side='left', ipady=6, ipadx=15)
        
        # Info Button
        info_btn = tk.Button(master_control_frame,
                            text="ℹ️ Hilfe",
                            command=self.show_server_help,
                            font=('Segoe UI', 10, 'bold'),
                            bg='#36393F',
                            fg='#B9BBBE',
                            activebackground='#40444B',
                            activeforeground='#FFFFFF',
                            relief='flat',
                            bd=0,
                            cursor='hand2')
        info_btn.pack(side='right', ipady=6, ipadx=15)
        
        # Initial laden
        self.refresh_server_list()
        
    def refresh_server_list(self):
        """Aktualisiert die Server-Liste"""
        # Alte Widgets entfernen
        for widget in self.server_list_frame.winfo_children():
            widget.destroy()
            
        for widget in self.master_list_frame.winfo_children():
            widget.destroy()
            
        if not bot or not bot_running:
            # Bot nicht verfügbar
            no_bot_label = tk.Label(self.server_list_frame,
                                   text="🤖 Bot muss gestartet sein\n\nStarte den Bot im 'Bot Status' Tab\num Server-Informationen zu sehen!",
                                   font=('Segoe UI', 11),
                                   fg='#B9BBBE',
                                   bg='#36393F',
                                   justify='center')
            no_bot_label.pack(expand=True)
            
            no_master_label = tk.Label(self.master_list_frame,
                                      text="🤖 Bot muss gestartet sein\n\nStarte den Bot um\nBerechtigungen zu verwalten!",
                                      font=('Segoe UI', 11),
                                      fg='#B9BBBE',
                                      bg='#36393F',
                                      justify='center')
            no_master_label.pack(expand=True)
            return
            
        # Server wo authentifizierter User Bot Master/Editor ist
        authorized_guilds = []
        for guild in bot.guilds:
            if (is_bot_admin(self.authenticated_user_id, guild.id) or 
                is_bot_editor(self.authenticated_user_id, guild.id)):
                authorized_guilds.append(guild)
        
        if not authorized_guilds:
            # Keine berechtigten Server
            no_auth_label = tk.Label(self.server_list_frame,
                                    text="🔒 Keine berechtigten Server\n\nDu bist auf keinem Server Bot Master oder Editor.\nVerwende '/setup_botmaster' auf Discord!",
                                    font=('Segoe UI', 11),
                                    fg='#B9BBBE',
                                    bg='#36393F',
                                    justify='center')
            no_auth_label.pack(expand=True)
            
            no_auth_master_label = tk.Label(self.master_list_frame,
                                           text="🔒 Keine Server-Berechtigungen\n\nNur Server wo du Bot Master/Editor bist\nwerden hier angezeigt!",
                                           font=('Segoe UI', 11),
                                           fg='#B9BBBE',
                                           bg='#36393F',
                                           justify='center')
            no_auth_master_label.pack(expand=True)
            return
        
        # Berechtigte Server anzeigen
        for guild in authorized_guilds:
            self.create_server_item(guild)
            
        # Bot Master Liste anzeigen (nur berechtigte Server)
        self.refresh_master_list(authorized_guilds)
        
    def create_server_item(self, guild):
        """Erstellt ein Widget für einen Server"""
        # Container für diesen Server
        item_frame = tk.Frame(self.server_list_frame, bg='#40444B', relief='flat', bd=1)
        item_frame.pack(fill='x', pady=3)
        
        # Hauptinhalt
        content_frame = tk.Frame(item_frame, bg='#40444B')
        content_frame.pack(fill='x', padx=12, pady=8)
        
        # Server Name und Info
        server_name = guild.name[:30] + "..." if len(guild.name) > 30 else guild.name
        
        name_label = tk.Label(content_frame,
                             text=f"🏠 {server_name}",
                             font=('Segoe UI', 11, 'bold'),
                             fg='#FFFFFF',
                             bg='#40444B')
        name_label.pack(anchor='w')
        
        # Server Details
        member_count = guild.member_count if guild.member_count else "?"
        channel_count = len(guild.text_channels) if guild.text_channels else 0
        
        details_text = f"👥 {member_count} Mitglieder • 💬 {channel_count} Text-Channels"
        
        details_label = tk.Label(content_frame,
                                text=details_text,
                                font=('Segoe UI', 9),
                                fg='#B9BBBE',
                                bg='#40444B')
        details_label.pack(anchor='w', pady=(2, 0))
        
        # Server ID (für Debugging)
        id_label = tk.Label(content_frame,
                           text=f"ID: {guild.id}",
                           font=('Consolas', 8),
                           fg='#72767D',
                           bg='#40444B')
        id_label.pack(anchor='w', pady=(2, 0))
        
    def load_bot_masters(self):
        """DEPRECATED - Ersetzt durch refresh_master_list mit Sicherheitsprüfung"""
        pass
            
    def create_master_section(self, guild_id, guild_data):
        """DEPRECATED - Ersetzt durch create_master_item mit Sicherheitsprüfung"""
        pass
        
    def refresh_master_list(self, authorized_guilds):
        """Zeigt Bot Master nur für berechtigte Server"""
        try:
            data_dir = os.path.join(APP_PATH, 'data')
            bot_roles_file = os.path.join(data_dir, 'bot_roles.json')
            
            bot_roles = {}
            if os.path.exists(bot_roles_file):
                with open(bot_roles_file, 'r', encoding='utf-8') as f:
                    bot_roles = json.load(f)
            
            if not bot_roles:
                no_master_label = tk.Label(self.master_list_frame,
                                          text="📭 Keine Bot Master konfiguriert\n\nVerwende '/setup_botmaster' auf Discord\num dich als Bot Master zu registrieren!",
                                          font=('Segoe UI', 11),
                                          fg='#B9BBBE',
                                          bg='#36393F',
                                          justify='center')
                no_master_label.pack(expand=True)
                return
            
            # Nur Bot Master für berechtigte Server anzeigen
            has_authorized_masters = False
            for guild in authorized_guilds:
                guild_str = str(guild.id)
                if guild_str in bot_roles:
                    has_authorized_masters = True
                    self.create_master_item(guild, bot_roles[guild_str])
            
            if not has_authorized_masters:
                no_auth_master_label = tk.Label(self.master_list_frame,
                                               text="🔒 Keine Bot Master-Daten\n\nFür deine berechtigten Server sind\nkeine Bot Master konfiguriert!",
                                               font=('Segoe UI', 11),
                                               fg='#B9BBBE',
                                               bg='#36393F',
                                               justify='center')
                no_auth_master_label.pack(expand=True)
                
        except Exception as e:
            error_label = tk.Label(self.master_list_frame,
                                  text=f"❌ Fehler beim Laden: {str(e)}",
                                  font=('Segoe UI', 11),
                                  fg='#ed4245',
                                  bg='#36393F')
            error_label.pack(expand=True)
            logging.error(f"Fehler beim Laden der Bot Master: {e}")
            
    def create_master_item(self, guild, roles_data):
        """Erstellt Widget für Bot Master/Editor Info eines Servers"""
        # Container für diesen Server
        item_frame = tk.Frame(self.master_list_frame, bg='#40444B', relief='flat', bd=1)
        item_frame.pack(fill='x', pady=5)
        
        # Server Header
        header_frame = tk.Frame(item_frame, bg='#40444B')
        header_frame.pack(fill='x', padx=15, pady=(10, 5))
        
        server_label = tk.Label(header_frame,
                               text=f"🏠 {guild.name}",
                               font=('Segoe UI', 11, 'bold'),
                               fg='#FFFFFF',
                               bg='#40444B')
        server_label.pack(anchor='w')
        
        # Bot Master
        master_id = roles_data.get('master')
        if master_id:
            try:
                master_user = bot.get_user(int(master_id))
                master_name = master_user.display_name if master_user else f"User ID: {master_id}"
            except:
                master_name = f"User ID: {master_id}"
                
            master_label = tk.Label(item_frame,
                                   text=f"👑 Bot Master: {master_name}",
                                   font=('Segoe UI', 10),
                                   fg='#FFD700',
                                   bg='#40444B')
            master_label.pack(anchor='w', padx=15)
        
        # Bot Editoren
        editors = roles_data.get('editors', [])
        if editors:
            editors_text = "✏️ Editoren: "
            editor_names = []
            for editor_id in editors:
                try:
                    editor_user = bot.get_user(int(editor_id))
                    editor_names.append(editor_user.display_name if editor_user else f"ID:{editor_id}")
                except:
                    editor_names.append(f"ID:{editor_id}")
            
            editors_text += ", ".join(editor_names)
            
            editors_label = tk.Label(item_frame,
                                    text=editors_text,
                                    font=('Segoe UI', 10),
                                    fg='#57F287',
                                    bg='#40444B')
            editors_label.pack(anchor='w', padx=15, pady=(0, 10))
        
    def show_server_help(self):
        """Zeigt Hilfe für Server-Verwaltung"""
        help_text = """🏠 Server Verwaltung Hilfe

📋 Server Liste:
• Zeigt alle Discord-Server wo der Bot Mitglied ist
• Mitglieder- und Channel-Anzahl
• Server-IDs für Debugging

👑 Bot Master & Editoren:
• Bot Master: Vollzugriff auf alle Bot-Funktionen
• Editoren: Können Sticky Messages verwalten

🔧 Discord Commands für Verwaltung:
• /setup_botmaster - Ersten Bot Master setzen
• /add_editor @user - Editor hinzufügen
• /remove_editor @user - Editor entfernen
• /list_roles - Alle Berechtigungen anzeigen
• /transfer_master @user - Bot Master übertragen

💡 Tipp: Jeder Server hat eigene Berechtigungen!"""

        messagebox.showinfo("🏠 Server Verwaltung Hilfe", help_text)

    def authenticate_user(self):
        """VERBESSERTE Discord Authentifizierung mit Fallback-Optionen"""
        try:
            self.add_log("🔐 Discord Authentifizierung wird gestartet...")
            
            # Discord Client ID aus .env laden
            client_id = os.getenv('DISCORD_CLIENT_ID')
            if not client_id:
                # Zeige erweiterte Konfigurationshilfe
                return self._show_oauth_setup_help()
                
            # Zeige Authentifizierungs-Optionen
            auth_choice = self._show_auth_choice_dialog()
            
            if auth_choice == "oauth":
                return self._try_oauth_auth(client_id)
            elif auth_choice == "manual":
                return self._try_manual_auth()
            elif auth_choice == "bypass":
                return self._try_bypass_auth()
            else:
                self.add_log("❌ Authentifizierung abgebrochen")
                return False
                
        except Exception as e:
            self.add_log(f"❌ Authentifizierung Fehler: {e}")
            return False
    
    def _show_oauth_setup_help(self):
        """Zeigt OAuth2 Setup-Hilfe"""
        import tkinter as tk
        from tkinter import messagebox
        
        help_text = (
            "❌ Discord Client-ID nicht konfiguriert!\n\n"
            "🔧 SETUP-ANLEITUNG:\n\n"
            "1. Gehe zu: https://discord.com/developers/applications\n"
            "2. Wähle deine Bot-Anwendung aus\n"
            "3. Kopiere die 'Application ID' (= Client-ID)\n"
            "4. Erstelle/bearbeite die .env Datei:\n"
            "   DISCORD_CLIENT_ID=deine_client_id_hier\n"
            "   DISCORD_TOKEN=dein_bot_token_hier\n\n"
            "5. Starte den Bot neu\n\n"
            "💡 Tipp: Du findest die .env Datei im Bot-Verzeichnis.\n"
            "Wenn sie nicht existiert, erstelle eine neue Textdatei namens '.env'"
        )
        
        result = messagebox.askyesno(
            "🔧 OAuth2 Setup erforderlich", 
            help_text + "\n\nMöchtest du stattdessen die manuelle Authentifizierung verwenden?"
        )
        
        if result:
            return self._try_manual_auth()
        return False
    
    def _show_auth_choice_dialog(self):
        """Zeigt Authentifizierungs-Auswahl Dialog"""
        import tkinter as tk
        from tkinter import messagebox
        
        # Erstelle Custom Dialog
        root = tk.Tk()
        root.withdraw()
        
        choice = messagebox.askyesnocancel(
            "🔐 Authentifizierung wählen",
            "🌐 OAUTH2 (Empfohlen)\n"
            "✅ Vollständig sicher über Discord\n"
            "✅ Automatische Berechtigungsprüfung\n"
            "✅ Professioneller Standard\n\n"
            "🔧 MANUELL (Alternative)\n"
            "⚠️ Eingabe von User-ID + Verification\n"
            "⚠️ Für Troubleshooting\n\n"
            "JA = OAuth2 | NEIN = Manuell | ABBRECHEN = Beenden"
        )
        
        root.destroy()
        
        if choice is True:
            return "oauth"
        elif choice is False:
            return "manual"
        else:
            return "cancel"
    
    def _try_oauth_auth(self, client_id):
        """OAuth2 Authentifizierung versuchen"""
        try:
            self.add_log("🌐 OAuth2 Authentifizierung wird gestartet...")
            
            # Prüfe OAuth2 Abhängigkeiten
            try:
                from src.utils.discord_oauth import DiscordOAuth
            except ImportError:
                self.add_log("❌ OAuth2 Abhängigkeiten fehlen")
                self.show_error_dialog(
                    "OAuth2 Fehler",
                    "OAuth2 Abhängigkeiten sind nicht installiert.\n\n"
                    "Führe aus: pip install requests flask jinja2"
                )
                return False
            
            # OAuth2 durchführen
            oauth = DiscordOAuth(client_id)
            success, result_data = oauth.start_auth_flow()
            
            if success:
                user_data = result_data
                user_name = f"{user_data['username']}#{user_data.get('discriminator', '0')}"
                authorized_count = len(user_data.get('authorized_guilds', []))
                
                self.add_log(f"🎉 OAuth2 erfolgreich für {user_name}")
                self.add_log(f"📊 Berechtigte Server: {authorized_count}")
                
                # In authorized_servers speichern
                self.authorized_servers = user_data.get('authorized_guilds', [])
                
                self.show_info_dialog(
                    "✅ Authentifizierung erfolgreich!",
                    f"OAuth2 erfolgreich für {user_name}\n\n"
                    f"Du hast Zugriff auf {authorized_count} Server als Bot-Master/Editor.\n"
                    f"Du kannst jetzt Sticky Messages verwalten!"
                )
                return True
            else:
                error_msg = result_data
                self.add_log(f"❌ OAuth2 fehlgeschlagen: {result_data}")
                
                # Spezielle Behandlung für 401 Fehler
                if "401" in str(error_msg):
                    self.show_error_dialog(
                        "OAuth2 Authentifizierung fehlgeschlagen",
                        "Bitte prüfe:\n\n"
                        "1. Discord Developer Portal → OAuth2 → Redirect URI:\n"
                        "   http://localhost:5000/callback\n\n"
                        "2. .env Datei:\n"
                        "   DISCORD_CLIENT_ID muss Application-ID sein\n\n"
                        "3. Verwende Alternative: 'Manuelle Authentifizierung'"
                    )
                else:
                    self.show_error_dialog("OAuth2 Fehler", str(error_msg))
                return False
            
        except Exception as e:
            self.add_log(f"❌ OAuth2 Fehler: {e}")
            self.show_error_dialog(
                "OAuth2 Fehler", 
                f"Unerwarteter Fehler:\n{str(e)}\n\n"
                "Verwende 'Manuelle Authentifizierung' als Alternative."
            )
            return False
    
    def _try_manual_auth(self):
        """Manuelle Authentifizierung versuchen"""
        try:
            self.add_log("🔧 Manuelle Authentifizierung wird gestartet...")
            
            # User-ID Dialog
            user_id = simpledialog.askstring(
                "Manuelle Authentifizierung",
                "Gib deine Discord User-ID ein:\n\n"
                "So findest du deine User-ID:\n"
                "1. Discord → Einstellungen → Erweitert\n"
                "2. 'Entwicklermodus' aktivieren\n"
                "3. Rechtsklick auf deinen Namen → 'ID kopieren'\n\n"
                "User-ID:",
                parent=self.root
            )
            
            if not user_id:
                return False
                
            if not user_id.isdigit():
                self.show_error_dialog("Ungültige User-ID", "User-ID muss eine Zahl sein!")
                return False
                
            # Validiere mit Bot (falls verfügbar)
            try:
                from src.utils.discord_auth import DiscordChallenge
                if hasattr(self, 'bot_instance') and self.bot_instance:
                    challenge = DiscordChallenge(self.bot_instance)
                    is_valid, user_info = challenge.validate_user_id(user_id)
                    
                    if is_valid:
                        self.add_log(f"✅ Manuelle Authentifizierung erfolgreich für User {user_id}")
                        
                        # User-Informationen sammeln 
                        username = user_info.get('display_name', f'User-{user_id}')
                        authorized_guilds = user_info.get('authorized_guilds', [])
                        
                        self.authorized_servers = authorized_guilds
                        
                        self.show_info_dialog(
                            "✅ Authentifizierung erfolgreich!",
                            f"Authentifiziert als: {username}\n\n"
                            f"Berechtigte Server: {len(authorized_guilds)}\n"
                            f"Du kannst jetzt Sticky Messages verwalten!"
                        )
                        return True
                    else:
                        self.show_error_dialog(
                            "Authentifizierung fehlgeschlagen",
                            "Du bist auf keinem Server als Bot-Master oder Editor registriert.\n\n"
                            "Verwende auf Discord:\n"
                            "• /setup_botmaster (falls noch kein Master existiert)\n"
                            "• Lass dich von einem Bot-Master als Editor hinzufügen"
                        )
                        return False
                else:
                    self.show_error_dialog(
                        "Bot nicht verfügbar",
                        "Bot muss gestartet sein für manuelle Authentifizierung.\n\n"
                        "Starte zuerst den Bot im 'Bot Status' Tab."
                    )
                    return False
                    
            except Exception as e:
                self.add_log(f"❌ Manuelle Authentifizierung Fehler: {e}")
                self.show_error_dialog("Authentifizierung Fehler", f"Fehler: {str(e)}")
                return False
            
        except Exception as e:
            self.show_error_dialog("Manuelle Authentifizierung Fehler", str(e))
            return False
    
    def _try_bypass_auth(self):
        """Bypass Authentifizierung für Entwicklungszwecke"""
        try:
            # Warnung anzeigen
            confirmed = messagebox.askyesno(
                "⚠️ Bypass Authentifizierung",
                "WARNUNG: Bypass-Modus überspringt Sicherheitsprüfungen!\n\n"
                "Verwende dies nur für Entwicklung/Tests.\n"
                "Alle Server werden als 'zugänglich' markiert.\n\n"
                "Trotzdem fortfahren?",
                parent=self.root
            )
            
            if confirmed:
                # Erstelle Mock-Daten
                self.authorized_servers = [
                    {'id': 'dev', 'name': 'Development Server', 'role': 'Bypass'}
                ]
                
                self.add_log("⚠️ Bypass Authentifizierung aktiviert")
                self.show_info_dialog(
                    "⚠️ Bypass Authentifizierung",
                    "Bypass-Modus aktiviert!\n\n"
                    "WARNUNG: Keine Sicherheitsprüfungen aktiv.\n"
                    "Nur für Entwicklung/Tests verwenden!"
                )
                return True
            else:
                return False
                
        except Exception as e:
            self.add_log(f"❌ Bypass Authentifizierung Fehler: {e}")
            return False

    def show_info_dialog(self, title, message):
        """Zeigt Info-Dialog an"""
        try:
            messagebox.showinfo(title, message, parent=self.root)
        except Exception as e:
            # Fallback auf Console falls GUI nicht verfügbar
            logging.error(f"❌ Info Dialog Fehler: {e}")

    def show_error_dialog(self, title, message):
        """Zeigt Error-Dialog an"""
        try:
            messagebox.showerror(title, message, parent=self.root)
        except Exception as e:
            # Fallback auf Console falls GUI nicht verfügbar
            logging.error(f"❌ Error Dialog Fehler: {e}")

    def get_user_authorized_servers(self, user_id):
        """Gibt Liste der Server zurück wo der User Bot Master/Editor ist"""
        try:
            from src.utils.permissions import get_user_authorized_guilds
            return get_user_authorized_guilds(user_id)
        except Exception as e:
            print(f"❌ Fehler beim Laden autorisierter Server: {e}")
            return []

def safe_print(message):
    """Sichere Print-Funktion für verschiedene Umgebungen"""
    try:
        logging.info(message)
    except:
        # Fallback für kritische Situationen
        safe_message = str(message).encode('utf-8', errors='replace').decode('utf-8')
        logging.info(safe_message)

def get_application_path():
    """Bestimmt den korrekten Anwendungspfad für .exe und Python"""
    if getattr(sys, 'frozen', False):
        # Bei .exe: Verzeichnis der .exe Datei
        app_path = os.path.dirname(sys.executable)
        logging.info(f"EXE Mode - Application Path: {app_path}")
    else:
        # Bei Python-Skript: Projektverzeichnis
        app_path = os.path.dirname(os.path.abspath(__file__))
        logging.info(f"Script Mode - Project Root: {app_path}")
    
    return app_path

def setup_paths():
    """Setup der Pfade für .exe und Python"""
    try:
        app_path = get_application_path()
        
        # Arbeitsverzeichnis auf App-Pfad setzen
        os.chdir(app_path)
        logging.info(f"Working Directory gesetzt auf: {app_path}")
        
        # Python-Path erweitern
        if app_path not in sys.path:
            sys.path.insert(0, app_path)
            
        logging.info(f"Python Path: {sys.path[:3]}...")  # Nur erste 3 für Übersicht
        
        # Wichtige Verzeichnisse erstellen falls sie nicht existieren
        data_dir = os.path.join(app_path, 'data')
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            logging.info(f"Data-Verzeichnis erstellt: {data_dir}")
        
        return app_path
        
    except Exception as e:
        logging.error(f"❌ Path Setup Fehler: {e}")
        logging.error(traceback.format_exc())
        return None

# Pfade früh einrichten
APP_PATH = setup_paths()

def get_token():
    """Token aus .env laden oder Setup starten"""
    try:
        logging.info("🔑 Token-Setup wird gestartet...")
        
        # .env Pfad relativ zum App-Pfad
        env_path = os.path.join(APP_PATH, '.env')
        logging.info(f".env Pfad: {env_path}")
        
        from dotenv import load_dotenv
        load_dotenv(env_path)  # Expliziter Pfad
        token = os.getenv('DISCORD_TOKEN')
        
        logging.info(f"Token aus .env geladen: {'✅ Ja' if token else '❌ Nein'}")
        
        if token and token != 'DEIN_BOT_TOKEN_HIER' and len(token) > 50:
            logging.info("✅ Gültiger Token gefunden")
            return token
        else:
            logging.info("🔧 Token Setup wird gestartet...")
            # Token Setup starten
            from src.utils.token_setup import setup_token
            if setup_token():
                # Nach Setup nochmal versuchen zu laden
                load_dotenv(env_path)
                new_token = os.getenv('DISCORD_TOKEN')
                logging.info(f"Token nach Setup: {'✅ Erhalten' if new_token else '❌ Nicht erhalten'}")
                return new_token
            else:
                logging.error("❌ Token Setup fehlgeschlagen")
                return None
                
    except Exception as e:
        logging.error(f"❌ Fehler beim Token-Setup: {e}")
        logging.error(traceback.format_exc())
        return None

def show_error_and_restart():
    """Zeigt Fehler an und startet Token-Setup neu"""
    try:
        logging.info("🔄 Error-Dialog wird angezeigt...")
        
        import tkinter as tk
        from tkinter import messagebox
        
        root = tk.Tk()
        root.withdraw()  # Hauptfenster verstecken
        
        result = messagebox.askyesno(
            "❌ Bot Login fehlgeschlagen!", 
            "Der Discord Bot Token ist ungültig oder falsch!\n\n"
            "Mögliche Ursachen:\n"
            "• Token ist abgelaufen oder wurde zurückgesetzt\n"
            "• Token gehört nicht zu einem Bot\n"
            "• Copy-Paste Fehler\n\n"
            "Möchtest du einen neuen Token eingeben?\n\n"
            "Debug-Log: sticky_bot_debug.log"
        )
        
        root.destroy()
        
        if result:
            logging.info("✅ User möchte neuen Token eingeben")
            # .env löschen um Setup zu erzwingen
            env_path = os.path.join(APP_PATH, '.env')
            if os.path.exists(env_path):
                os.remove(env_path)
                logging.info("🗑️ .env Datei gelöscht")
            return True
        else:
            logging.info("❌ User hat abgebrochen")
            return False
            
    except Exception as e:
        logging.error(f"❌ Error-Dialog Fehler: {e}")
        logging.error(traceback.format_exc())
        
        # Fallback ohne GUI
        safe_print("\n" + "="*60)
        safe_print("❌ BOT LOGIN FEHLGESCHLAGEN!")
        safe_print("="*60)
        safe_print("Der Discord Token ist ungültig!")
        safe_print("\nMögliche Ursachen:")
        safe_print("• Token ist abgelaufen oder wurde zurückgesetzt")
        safe_print("• Token gehört nicht zu einem Bot")
        safe_print("• Copy-Paste Fehler")
        safe_print(f"\nDebug-Log: {os.path.join(APP_PATH, 'sticky_bot_debug.log')}")
        safe_print("\nBitte starte den Bot neu für ein neues Setup.")
        safe_print("="*60)
        input("\nDrücke Enter zum Beenden...")
        return False

# Token beim Start laden
try:
    logging.info("🔑 Token wird geladen...")
    TOKEN = get_token()
    if not TOKEN:
        logging.error("❌ Bot-Start abgebrochen - kein gültiger Token!")
        safe_print("❌ Bot-Start abgebrochen - kein gültiger Token!")
        if not getattr(sys, 'frozen', False):
            input("Drücke Enter zum Beenden...")
        sys.exit(1)
    
    logging.info("✅ Token erfolgreich geladen")
    
except Exception as e:
    logging.error(f"❌ Kritischer Fehler beim Token-Setup: {e}")
    safe_print(f"❌ Kritischer Fehler: {e}")
    safe_print(f"Debug-Log: {os.path.join(APP_PATH, 'sticky_bot_debug.log')}")
    if not getattr(sys, 'frozen', False):
        input("Drücke Enter zum Beenden...")
    sys.exit(1)

# Bot Setup
try:
    logging.info("🤖 Discord Bot wird initialisiert...")
    
    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix='/', intents=intents)
    
    logging.info("✅ Bot erfolgreich initialisiert")
    
except Exception as e:
    logging.error(f"❌ Bot Initialisierung fehlgeschlagen: {e}")
    logging.error(traceback.format_exc())
    safe_print(f"❌ Bot Initialisierung fehlgeschlagen: {e}")
    input("Drücke Enter zum Beenden...")
    sys.exit(1)

# Liste der Cogs die geladen werden sollen
INITIAL_EXTENSIONS = [
    'src.cogs.admin',
    'src.cogs.sticky',
    'src.cogs.events',
    'src.cogs.help'
]

# Bot Event Handlers für Status-Updates
@bot.event
async def on_ready():
    global bot_running
    logging.info(f'✅ Bot ist eingeloggt als {bot.user}')
    safe_print(f'✅ Bot ist eingeloggt als {bot.user}')
    
    bot_running = True
    
    if status_window:
        status_window.update_status(
            f"✅ Bot online: {bot.user.name}",
            f"Verbunden mit {len(bot.guilds)} Server(n)",
            "#00b894"
        )
        status_window.add_log(f"✅ Bot erfolgreich gestartet als {bot.user.name}")
        status_window.add_log(f"📊 Verbunden mit {len(bot.guilds)} Discord-Server(n)")
        
        # Buttons aktualisieren
        status_window.start_btn.config(state='disabled')
        status_window.stop_btn.config(state='normal')
        
        # Liste der Server anzeigen
        for guild in bot.guilds:
            status_window.add_log(f"🏠 Server: {guild.name} ({guild.member_count} Mitglieder)")

@bot.event
async def on_disconnect():
    logging.warning("⚠️ Bot wurde getrennt")
    safe_print("⚠️ Bot wurde getrennt")
    
    if status_window:
        status_window.update_status(
            "⚠️ Bot getrennt",
            "Verbindung zu Discord verloren",
            "#FAA61A"
        )
        status_window.add_log("⚠️ Verbindung zu Discord verloren")

@bot.event
async def on_resumed():
    logging.info("🔄 Bot-Verbindung wiederhergestellt")
    safe_print("🔄 Bot-Verbindung wiederhergestellt")
    
    if status_window:
        status_window.update_status(
            f"✅ Bot online: {bot.user.name}",
            "Verbindung wiederhergestellt",
            "#00b894"
        )
        status_window.add_log("🔄 Verbindung zu Discord wiederhergestellt")

async def load_extensions():
    logging.info("📦 Extensions werden geladen...")
    
    for extension in INITIAL_EXTENSIONS:
        try:
            await bot.load_extension(extension)
            logging.info(f'✅ Loaded extension {extension}')
            safe_print(f'✅ Loaded extension {extension}')
            
            # Debug: Liste alle Commands des Cogs
            cog = bot.get_cog(extension.split('.')[-1].capitalize() + 'Cog')
            if cog:
                commands_list = [cmd.name for cmd in cog.get_app_commands()]
                logging.info(f"Commands in {extension}: {commands_list}")
                
        except Exception as e:
            logging.error(f'❌ Failed to load extension {extension}: {e}')
            logging.error(traceback.format_exc())
            safe_print(f'❌ Failed to load extension {extension}: {e}')

async def run_bot():
    """Läuft den Bot in einem separaten Thread"""
    global bot_running
    
    logging.info("🚀 Bot wird gestartet...")
    safe_print("🚀 Starte Sticky-Bot...")
    
    try:
        async with bot:
            await load_extensions()
            logging.info("🌐 Bot Login wird versucht...")
            if status_window:
                status_window.add_log("🌐 Verbinde mit Discord...")
            await bot.start(TOKEN)
            
    except discord.LoginFailure as e:
        logging.error(f'❌ Bot Login fehlgeschlagen - Ungültiger Token: {e}')
        bot_running = False
        
        if status_window:
            status_window.update_status(
                "❌ Login fehlgeschlagen",
                "Ungültiger Discord Token",
                "#ed4245"
            )
            status_window.add_log("❌ Bot Login fehlgeschlagen - Token ungültig!")
            # Buttons zurücksetzen
            status_window.start_btn.config(state='normal')
            status_window.stop_btn.config(state='disabled')
        
        # Token Setup neu starten wenn gewünscht
        if show_error_and_restart():
            logging.info("🔄 Bot wird neu gestartet...")
            safe_print("🔄 Bot wird neu gestartet...")
            # .exe neu starten (wenn kompiliert)
            if getattr(sys, 'frozen', False):
                os.execv(sys.executable, sys.argv)
            else:
                # Python Skript neu starten
                os.execv(sys.executable, [sys.executable] + sys.argv)
        else:
            logging.info("👋 Bot beendet!")
            safe_print("👋 Bot beendet!")
            
    except discord.HTTPException as e:
        bot_running = False
        
        if "401" in str(e) or "Unauthorized" in str(e):
            logging.error(f'❌ 401 Unauthorized - Token ungültig: {e}')
            if status_window:
                status_window.update_status(
                    "❌ Unauthorized",
                    "Token ungültig oder abgelaufen",
                    "#ed4245"
                )
                status_window.add_log("❌ 401 Unauthorized - Token ungültig!")
                # Buttons zurücksetzen
                status_window.start_btn.config(state='normal')
                status_window.stop_btn.config(state='disabled')
            
            # Gleiche Behandlung wie LoginFailure
            if show_error_and_restart():
                logging.info("🔄 Bot wird neu gestartet...")
                safe_print("🔄 Bot wird neu gestartet...")
                if getattr(sys, 'frozen', False):
                    os.execv(sys.executable, sys.argv)
                else:
                    os.execv(sys.executable, [sys.executable] + sys.argv)
            else:
                logging.info("👋 Bot beendet!")
                safe_print("👋 Bot beendet!")
        else:
            logging.error(f'❌ HTTP Fehler: {e}')
            logging.error(traceback.format_exc())
            safe_print(f"❌ HTTP Fehler: {e}")
            if status_window:
                status_window.update_status(
                    "❌ HTTP Fehler",
                    str(e),
                    "#ed4245"
                )
                status_window.add_log(f"❌ HTTP Fehler: {e}")
                # Buttons zurücksetzen
                status_window.start_btn.config(state='normal')
                status_window.stop_btn.config(state='disabled')
                
    except Exception as e:
        logging.error(f'❌ Ein unerwarteter Fehler ist aufgetreten: {e}')
        logging.error(traceback.format_exc())
        safe_print(f"❌ Ein unerwarteter Fehler ist aufgetreten: {e}")
        bot_running = False
        
        if status_window:
            status_window.update_status(
                "❌ Unerwarteter Fehler",
                str(e),
                "#ed4245"
            )
            status_window.add_log(f"❌ Unerwarteter Fehler: {e}")
            # Buttons zurücksetzen
            status_window.start_btn.config(state='normal')
            status_window.stop_btn.config(state='disabled')

def start_bot_thread():
    """Startet den Bot in einem separaten Thread"""
    def run_async_bot():
        try:
            asyncio.run(run_bot())
        except KeyboardInterrupt:
            logging.info('👋 Bot wurde durch Benutzer beendet')
        except Exception as e:
            logging.error(f"❌ Bot Thread Fehler: {e}")
            if status_window:
                status_window.add_log(f"❌ Bot Thread Fehler: {e}")
        finally:
            global bot_running
            bot_running = False
            if status_window:
                # Buttons zurücksetzen
                status_window.start_btn.config(state='normal')
                status_window.stop_btn.config(state='disabled')
    
    bot_thread = threading.Thread(target=run_async_bot, daemon=True)
    bot_thread.start()
    return bot_thread

if __name__ == "__main__":
    try:
        # Hauptprogramm starten mit GUI
        logging.info("🎬 Sticky-Bot GUI wird gestartet...")
        
        # GUI Setup
        logging.info("📋 GUI wird initialisiert...")
        status_window = BotStatusWindow()
        
        logging.info("✅ GUI erfolgreich erstellt!")
        
        # Event Loop starten
        logging.info("🖥️ GUI-Hauptschleife wird gestartet...")
        status_window.run()
        
    except Exception as e:
        logging.error(f"❌ Ein unerwarteter Fehler ist aufgetreten: {e}")
        safe_print(f"❌ Ein unerwarteter Fehler ist aufgetreten: {e}")
        if not getattr(sys, 'frozen', False):
            input("Drücke Enter zum Beenden...")
    finally:
        # Aufräumen
        logging.info("=== STICKY-BOT DEBUG END ===")
        safe_print("👋 Bot beendet!")
