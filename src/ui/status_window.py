"""
Hauptfenster für Sticky-Bot Kontrollzentrum
"""
import tkinter as tk
from tkinter import messagebox, simpledialog
import threading
import os
import sys
from datetime import datetime
from PIL import Image, ImageTk
import logging
from dotenv import load_dotenv

from src.config.constants import WINDOW_CONFIG, TAB_CONFIG
from src.ui.sticky_dialog import StickyManagerDialog
from src.ui.tabs.status_tab import StatusTab
from src.ui.tabs.sticky_tab import StickyTab
from src.ui.tabs.server_tab import ServerTab
from src.utils.path_manager import get_application_path


class BotStatusWindow:
    def __init__(self):
        self.authenticated_user = None
        self.authenticated_user_id = None
        self.current_tab = 'status'
        
        # GUI erst erstellen
        self.root = tk.Tk()
        self.root.title(WINDOW_CONFIG['title'])
        self.root.geometry(WINDOW_CONFIG['geometry'])
        self.root.resizable(True, True)
        
        # Icon versuchen zu setzen
        try:
            self.root.iconbitmap('icon.ico')
        except:
            pass
        
        # Modernes Theme
        self.root.configure(bg=WINDOW_CONFIG['colors']['background'])
        
        # Zentrieren
        self.root.eval('tk::PlaceWindow . center')
        
        # Hintergrundbild laden
        self.background_image = None
        self.load_background()
        
        # Tab-Module initialisieren
        self.status_tab = None
        self.sticky_tab = None
        self.server_tab = None
        
        self.setup_gui()
        
        # Beim Schließen des Fensters den Bot beenden
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
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
        self.tab_frame = tk.Frame(self.root, bg=WINDOW_CONFIG['colors']['background'])
        self.tab_frame.pack(fill='x', padx=10, pady=(10, 0))
        
        # Tab Buttons erstellen
        self.create_tab_buttons()
        
        # Content Frame für die Tab-Inhalte
        self.content_frame = tk.Frame(self.root, bg=WINDOW_CONFIG['colors']['background'])
        self.content_frame.pack(fill='both', expand=True, padx=10, pady=(5, 10))
        
        # Tab-Module initialisieren
        self.status_tab = StatusTab(self.content_frame, self)
        self.sticky_tab = StickyTab(self.content_frame, self)
        self.server_tab = ServerTab(self.content_frame, self)
        
        # Authentifizierung Section hinzufügen
        self.setup_auth_section()
        
        # Standard: Status Tab aktiv
        self.switch_tab('status')
        
    def create_tab_buttons(self):
        """Erstellt die Tab-Navigation Buttons mit verbesserter Sichtbarkeit"""
        colors = WINDOW_CONFIG['colors']
        
        # Status Tab Button
        self.status_tab_btn = tk.Button(
            self.tab_frame,
            text=TAB_CONFIG['status']['title'],
            command=lambda: self.switch_tab('status'),
            font=('Segoe UI', 12, 'bold'),
            bg=TAB_CONFIG['status']['color'],
            fg=colors['button_text'],
            activebackground=TAB_CONFIG['status']['hover'],
            activeforeground=colors['button_text'],
            relief='raised',
            bd=2,
            cursor='hand2',
            height=1
        )
        self.status_tab_btn.pack(side='left', fill='x', expand=True, ipady=10, padx=(0, 2))
        
        # Sticky Tab Button  
        self.sticky_tab_btn = tk.Button(
            self.tab_frame,
            text=TAB_CONFIG['sticky']['title'],
            command=lambda: self.switch_tab('sticky'),
            font=('Segoe UI', 12, 'bold'),
            bg=colors['secondary'],
            fg=colors['text_secondary'],
            activebackground=colors['secondary_hover'],
            activeforeground=colors['button_text'],
            relief='raised',
            bd=2,
            cursor='hand2',
            height=1
        )
        self.sticky_tab_btn.pack(side='left', fill='x', expand=True, ipady=10, padx=(2, 2))
        
        # Server Tab Button
        self.server_tab_btn = tk.Button(
            self.tab_frame,
            text=TAB_CONFIG['server']['title'],
            command=lambda: self.switch_tab('server'),
            font=('Segoe UI', 12, 'bold'),
            bg=colors['secondary'],
            fg=colors['text_secondary'],
            activebackground=colors['secondary_hover'],
            activeforeground=colors['button_text'],
            relief='raised',
            bd=2,
            cursor='hand2',
            height=1
        )
        self.server_tab_btn.pack(side='right', fill='x', expand=True, ipady=10, padx=(2, 0))
        
        # Hover-Effekte für Tab-Buttons
        self._add_tab_hover_effects()

    def _add_tab_hover_effects(self):
        # Implementiere Hover-Effekte für Tab-Buttons
        pass

    def switch_tab(self, tab_name):
        """Wechselt zwischen den Tabs"""
        colors = WINDOW_CONFIG['colors']
        
        # Spezielle Behandlung für geschützte Tabs - Authentifizierung erforderlich
        if tab_name in ['sticky', 'server']:
            # Prüfe ob bereits authentifiziert
            if not self.authenticated_user_id:
                # Zeige freundlichen Hinweis anstatt OAuth-Zwang
                try:
                    import tkinter.messagebox as msgbox
                    result = msgbox.askquestion(
                        "🔐 Authentifizierung erforderlich",
                        "Für diesen Tab benötigst du eine Discord-Anmeldung.\n\n"
                        "Möchtest du dich jetzt anmelden?\n\n"
                        "Wähle 'Yes' für OAuth oder 'No' um zum Status-Tab zurückzukehren.",
                        parent=self.root
                    )
                    
                    if result == 'yes':
                        # Wechsle zurück zum Status Tab für OAuth
                        tab_name = 'status'
                        if hasattr(self, 'status_tab') and self.status_tab:
                            # Challenge-Response System nur wenn wirklich nötig
                            success = self.authenticate_user()
                            if not success:
                                return  # Authentifizierung abgebrochen
                        else:
                            return
                    else:
                        # Bleibe beim aktuellen Tab oder gehe zu Status
                        if not hasattr(self, 'current_tab') or not self.current_tab:
                            tab_name = 'status'
                        else:
                            return  # Bleibe beim aktuellen Tab
                        
                except Exception as auth_error:
                    logging.error(f"❌ Auth-Dialog Fehler: {auth_error}")
                    return
        
        self.current_tab = tab_name
        
        # Alle Tabs verstecken
        if self.status_tab:
            self.status_tab.hide()
        if self.sticky_tab:
            self.sticky_tab.hide()
        if self.server_tab:
            self.server_tab.hide()
        
        # Aktiven Tab anzeigen
        if tab_name == 'status':
            if not self.status_tab:
                from src.ui.tabs.status_tab import StatusTab
                self.status_tab = StatusTab(self.content_frame, self)
            self.status_tab.show()
            
        elif tab_name == 'sticky':
            if not self.sticky_tab:
                from src.ui.tabs.sticky_tab import StickyTab
                self.sticky_tab = StickyTab(self.content_frame, self)
            self.sticky_tab.show()
            
        elif tab_name == 'server':
            if not self.server_tab:
                from src.ui.tabs.server_tab import ServerTab
                self.server_tab = ServerTab(self.content_frame, self)
            self.server_tab.show()
        
        # Tab-Button Farben aktualisieren
        # Status Tab
        if tab_name == 'status':
            self.status_tab_btn.config(bg=colors['primary'])
        else:
            self.status_tab_btn.config(bg=colors['secondary'])
        
        # Sticky Tab  
        if tab_name == 'sticky':
            self.sticky_tab_btn.config(bg=colors['success'])
        else:
            self.sticky_tab_btn.config(bg=colors['secondary'])
        
        # Server Tab
        if tab_name == 'server':
            self.server_tab_btn.config(bg=colors['warning'])
        else:
            self.server_tab_btn.config(bg=colors['secondary'])

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
                    "Führe aus: pip install requests flask"
                )
                return
            
            # OAuth Client initialisieren
            oauth = DiscordOAuth(client_id)
            
            # Authentifizierung starten
            result = oauth.start_auth_flow()
            
            if result and 'user_id' in result:
                # Erfolgreiche Authentifizierung
                self.authenticated_user_id = result['user_id']
                self.authenticated_username = result.get('username', 'Unbekannt')
                
                self.add_log(f"✅ Discord OAuth2 Authentifizierung erfolgreich")
                self.add_log(f"👤 Angemeldet als: {self.authenticated_username}")
                
                # UI aktualisieren
                self.update_auth_status()
                
                return True
            else:
                self.add_log("❌ OAuth2 Authentifizierung fehlgeschlagen")
                return False
                
        except Exception as e:
            logging.error(f"OAuth2 Fehler: {e}")
            self.add_log(f"❌ OAuth2 Fehler: {str(e)}")
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
            
            if not user_id or not user_id.isdigit():
                return False
                
            self.authenticated_user_id = int(user_id)
            self.add_log(f"✅ Manuelle Authentifizierung für User {user_id}")
            return True
            
        except Exception as e:
            self.show_error_dialog("Manuelle Authentifizierung Fehler", str(e))
            return False
    
    def _try_bypass_auth(self):
        """Bypass Authentifizierung für Entwicklungszwecke"""
        try:
            confirmed = messagebox.askyesno(
                "⚠️ Bypass Authentifizierung",
                "WARNUNG: Bypass-Modus überspringt Sicherheitsprüfungen!\n\n"
                "Verwende dies nur für Entwicklung/Tests.\n"
                "Alle Server werden als 'zugänglich' markiert.\n\n"
                "Trotzdem fortfahren?",
                parent=self.root
            )
            
            if confirmed:
                self.authenticated_user_id = 123456789  # Mock User ID
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
            logging.error(f"❌ Info Dialog Fehler: {e}")

    def show_error_dialog(self, title, message):
        """Zeigt Error-Dialog an"""
        try:
            messagebox.showerror(title, message, parent=self.root)
        except Exception as e:
            logging.error(f"❌ Error Dialog Fehler: {e}")

    def add_log(self, message):
        """Fügt eine Log-Nachricht hinzu - delegiert an Status Tab"""
        if self.status_tab:
            self.status_tab.add_log(message)
        
    def update_status(self, status, info="", color="#FAA61A"):
        """Aktualisiert den Bot-Status - delegiert an Status Tab"""
        if self.status_tab:
            self.status_tab.update_status(status, info, color)
            
    def on_closing(self):
        """Wird beim Schließen des Fensters aufgerufen"""
        result = messagebox.askyesno("🤔 Programm beenden?", 
                                   "Möchtest du den Sticky-Bot wirklich beenden?\n"
                                   "Alle Sticky Messages werden gestoppt.")
        if result:
            self.add_log("👋 Programm wird beendet...")
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

    def on_bot_ready(self):
        """Wird aufgerufen wenn der Bot bereit ist"""
        try:
            # Einfache Aktualisierung ohne UI-Manipulation
            # Da die UI-Struktur komplex ist, machen wir nur grundlegende Updates
            
            # Bot Manager referenz prüfen
            if hasattr(self, 'bot_manager') and self.bot_manager:
                # Status-Update über bot_manager
                if hasattr(self.bot_manager, 'bot') and self.bot_manager.bot:
                    bot_name = self.bot_manager.bot.user.name if self.bot_manager.bot.user else "Bot"
                    guild_count = len(self.bot_manager.bot.guilds) if self.bot_manager.bot.guilds else 0
                    
                    self.add_log(f"🎉 Bot '{bot_name}' erfolgreich gestartet!")
                    self.add_log(f"📊 Verbunden mit {guild_count} Discord-Server(n)")
            
            # Keine UI-Button-Manipulation mehr, da das zu komplex ist
            
        except Exception as e:
            # Minimaler Error Log
            pass
            
    def refresh_server_data(self):
        """Aktualisiert Server-Daten nach Bot-Start"""
        try:
            # Einfache Server-Daten Aktualisierung
            if hasattr(self, 'bot_manager') and self.bot_manager and hasattr(self.bot_manager, 'bot'):
                if self.bot_manager.bot and self.bot_manager.bot.guilds:
                    for guild in self.bot_manager.bot.guilds:
                        self.add_log(f"🏠 Server: {guild.name} ({guild.member_count} Mitglieder)")
        except Exception:
            pass

    def setup_auth_section(self):
        """Setup der Authentifizierungs-Sektion mit verbesserter Sichtbarkeit"""
        colors = WINDOW_CONFIG['colors']
        
        # Authentifizierung Frame
        auth_frame = tk.LabelFrame(self.root, text="🔐 Discord Authentifizierung", 
                                  font=('Segoe UI', 12, 'bold'),
                                  fg=colors['text_primary'], bg=colors['background'],
                                  bd=2, relief='raised')
        auth_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        # Info Label
        self.auth_info = tk.Label(auth_frame, 
                                 text="Nicht authentifiziert - Melde dich an um alle Features zu nutzen!",
                                 font=('Segoe UI', 10),
                                 fg=colors['warning'], bg=colors['background'])
        self.auth_info.pack(pady=(10, 15), padx=10)
        
        # Button Frame
        auth_button_frame = tk.Frame(auth_frame, bg=colors['background'])
        auth_button_frame.pack(fill='x', padx=10, pady=(0, 15))
        
        # OAuth Login Button
        self.oauth_btn = tk.Button(auth_button_frame, text="🌐 Discord OAuth Login",
                                  command=self.start_oauth_auth,
                                  font=('Segoe UI', 11, 'bold'),
                                  bg=colors['primary'], fg=colors['button_text'],
                                  activebackground=colors['primary_hover'],
                                  activeforeground=colors['button_text'],
                                  relief='raised', bd=2, cursor='hand2',
                                  state='normal')
        self.oauth_btn.pack(side='left', ipady=10, ipadx=20)
        
        # Manual Auth Button
        self.manual_btn = tk.Button(auth_button_frame, text="🔧 Manuelle Authentifizierung",
                                   command=self.start_manual_auth,
                                   font=('Segoe UI', 11, 'bold'),
                                   bg=colors['warning'], fg=colors['button_text'],
                                   activebackground=colors['warning_hover'],
                                   activeforeground=colors['button_text'],
                                   relief='raised', bd=2, cursor='hand2')
        self.manual_btn.pack(side='left', padx=(15, 0), ipady=10, ipadx=20)
        
        # Logout Button
        self.logout_btn = tk.Button(auth_button_frame, text="🚪 Abmelden",
                                   command=self.logout_user,
                                   font=('Segoe UI', 11, 'bold'),
                                   bg=colors['error'], fg=colors['button_text'],
                                   activebackground=colors['error_hover'],
                                   activeforeground=colors['button_text'],
                                   relief='raised', bd=2, cursor='hand2',
                                   state='disabled')
        self.logout_btn.pack(side='right', ipady=10, ipadx=20)
        
        # Hover-Effekte hinzufügen
        self._add_auth_hover_effects()
    
    def _add_auth_hover_effects(self):
        """Fügt Hover-Effekte zu den Auth-Buttons hinzu"""
        colors = WINDOW_CONFIG['colors']
        
        # OAuth Button Hover
        def oauth_enter(event):
            if self.oauth_btn['state'] == 'normal':
                self.oauth_btn.config(bg=colors['primary_hover'])
        def oauth_leave(event):
            if self.oauth_btn['state'] == 'normal':
                self.oauth_btn.config(bg=colors['primary'])
        
        # Manual Button Hover
        def manual_enter(event):
            if self.manual_btn['state'] == 'normal':
                self.manual_btn.config(bg=colors['warning_hover'])
        def manual_leave(event):
            if self.manual_btn['state'] == 'normal':
                self.manual_btn.config(bg=colors['warning'])
        
        # Logout Button Hover
        def logout_enter(event):
            if self.logout_btn['state'] == 'normal':
                self.logout_btn.config(bg=colors['error_hover'])
        def logout_leave(event):
            if self.logout_btn['state'] == 'normal':
                self.logout_btn.config(bg=colors['error'])
        
        # Bind Events
        self.oauth_btn.bind("<Enter>", oauth_enter)
        self.oauth_btn.bind("<Leave>", oauth_leave)
        self.manual_btn.bind("<Enter>", manual_enter)
        self.manual_btn.bind("<Leave>", manual_leave)
        self.logout_btn.bind("<Enter>", logout_enter)
        self.logout_btn.bind("<Leave>", logout_leave)

    def start_oauth_auth(self):
        """Startet OAuth Authentifizierung mit verbesserter Fehlerbehandlung"""
        try:
            self.add_log("🔐 Discord OAuth Authentifizierung wird gestartet...")
            
            # Prüfe .env für Client ID
            env_path = os.path.join(get_application_path(), '.env')
            load_dotenv(env_path)
            
            client_id = os.getenv('DISCORD_CLIENT_ID')
            client_secret = os.getenv('DISCORD_CLIENT_SECRET')
            
            if not client_id:
                self.add_log("❌ Client ID nicht konfiguriert!")
                self._show_oauth_setup_dialog(env_path)
                return
            
            self.oauth_btn.config(state='disabled', text="🔄 OAuth läuft...")
            
            def run_oauth():
                try:
                    from src.utils.discord_oauth import DiscordOAuth
                    oauth = DiscordOAuth(client_id, client_secret)
                    success, result = oauth.start_auth_flow()
                    
                    if success:
                        user_info = result
                        user_id = user_info.get('id')
                        username = user_info.get('username', 'Unbekannt')
                        
                        # Setze authentifizierten User
                        self.authenticated_user_id = int(user_id)
                        
                        self.add_log(f"✅ OAuth erfolgreich! Angemeldet als: {username}")
                        
                        # UI Update im Main Thread
                        self.root.after(0, lambda: self.update_auth_ui(username))
                        
                    else:
                        self.add_log(f"❌ OAuth fehlgeschlagen: {result}")
                        self.root.after(0, lambda: messagebox.showerror("OAuth Fehler", f"Authentifizierung fehlgeschlagen:\n\n{result}"))
                        
                except Exception as e:
                    self.add_log(f"❌ OAuth Fehler: {e}")
                    self.root.after(0, lambda: messagebox.showerror("OAuth Fehler", f"Unerwarteter Fehler:\n\n{str(e)}"))
                finally:
                    # Button wieder aktivieren
                    self.root.after(0, lambda: self.oauth_btn.config(state='normal', text="🌐 Discord OAuth Login"))
            
            # OAuth in separatem Thread starten
            import threading
            auth_thread = threading.Thread(target=run_oauth, daemon=True)
            auth_thread.start()
            
        except Exception as e:
            self.add_log(f"❌ OAuth Setup Fehler: {e}")
            messagebox.showerror("Fehler", f"OAuth Setup Fehler:\n\n{str(e)}")
            self.oauth_btn.config(state='normal', text="🌐 Discord OAuth Login")

    def _show_oauth_setup_dialog(self, env_path):
        """Zeigt einen detaillierten OAuth Setup Dialog"""
        colors = WINDOW_CONFIG['colors']
        
        # Setup Dialog erstellen
        setup_dialog = tk.Toplevel(self.root)
        setup_dialog.title("🔧 OAuth Setup erforderlich")
        setup_dialog.geometry("650x500")
        setup_dialog.configure(bg=colors['background'])
        setup_dialog.grab_set()
        setup_dialog.resizable(False, False)
        
        # Zentrieren
        setup_dialog.transient(self.root)
        
        # Header
        header_frame = tk.Frame(setup_dialog, bg=colors['primary'])
        header_frame.pack(fill='x', pady=(0, 20))
        
        header_label = tk.Label(header_frame, 
                               text="🔧 Discord OAuth Setup", 
                               font=('Segoe UI', 16, 'bold'),
                               fg=colors['button_text'], bg=colors['primary'])
        header_label.pack(pady=15)
        
        # Main Content
        main_frame = tk.Frame(setup_dialog, bg=colors['background'])
        main_frame.pack(fill='both', expand=True, padx=20)
        
        # Anleitung Text
        instruction_text = (
            "❌ Discord Client ID ist nicht konfiguriert!\n\n"
            "🔧 SO KONFIGURIERST DU OAUTH2:\n\n"
            "1️⃣ Gehe zu: https://discord.com/developers/applications\n"
            "2️⃣ Wähle deine Bot-Anwendung aus\n"
            "3️⃣ Klicke auf 'General Information'\n"
            "4️⃣ Kopiere die 'Application ID' (= Client ID)\n"
            "5️⃣ Bearbeite die .env Datei und füge hinzu:\n"
            "    DISCORD_CLIENT_ID=deine_application_id_hier\n\n"
            "💡 OPTIONAL für erweiterte Features:\n"
            "    DISCORD_CLIENT_SECRET=dein_client_secret\n\n"
            "⚠️ WICHTIG: Starte den Bot nach der Änderung neu!"
        )
        
        instruction_label = tk.Label(main_frame, text=instruction_text,
                                    font=('Segoe UI', 11),
                                    fg=colors['text_primary'], bg=colors['background'],
                                    justify='left', wraplength=600)
        instruction_label.pack(pady=(0, 20))
        
        # .env Pfad anzeigen
        path_frame = tk.Frame(main_frame, bg=colors['secondary'], relief='sunken', bd=2)
        path_frame.pack(fill='x', pady=(0, 20))
        
        path_label = tk.Label(path_frame, 
                             text=f"📁 .env Datei Pfad:\n{env_path}",
                             font=('Segoe UI', 10),
                             fg=colors['text_primary'], bg=colors['secondary'])
        path_label.pack(pady=10, padx=10)
        
        # Button Frame
        button_frame = tk.Frame(main_frame, bg=colors['background'])
        button_frame.pack(fill='x', pady=(0, 20))
        
        # Developer Portal Button
        def open_discord_dev():
            import webbrowser
            webbrowser.open('https://discord.com/developers/applications')
        
        dev_btn = tk.Button(button_frame, text="🌐 Discord Developer Portal öffnen",
                           command=open_discord_dev,
                           font=('Segoe UI', 11, 'bold'),
                           bg=colors['primary'], fg=colors['button_text'],
                           relief='raised', bd=2, cursor='hand2')
        dev_btn.pack(side='left', ipady=8, ipadx=15)
        
        # .env öffnen Button
        def open_env_file():
            try:
                os.startfile(env_path)
            except:
                try:
                    import subprocess
                    subprocess.run(['notepad.exe', env_path])
                except:
                    messagebox.showinfo("Datei öffnen", f"Bitte öffne die .env Datei manuell:\n\n{env_path}")
        
        env_btn = tk.Button(button_frame, text="📝 .env Datei bearbeiten",
                           command=open_env_file,
                           font=('Segoe UI', 11, 'bold'),
                           bg=colors['warning'], fg=colors['button_text'],
                           relief='raised', bd=2, cursor='hand2')
        env_btn.pack(side='left', padx=(10, 0), ipady=8, ipadx=15)
        
        # Manuelle Auth Button
        def use_manual_auth():
            setup_dialog.destroy()
            self.start_manual_auth()
        
        manual_btn = tk.Button(button_frame, text="🔧 Manuelle Authentifizierung",
                              command=use_manual_auth,
                              font=('Segoe UI', 11, 'bold'),
                              bg=colors['success'], fg=colors['button_text'],
                              relief='raised', bd=2, cursor='hand2')
        manual_btn.pack(side='right', ipady=8, ipadx=15)
        
        # Schließen Button
        close_btn = tk.Button(button_frame, text="❌ Schließen",
                             command=setup_dialog.destroy,
                             font=('Segoe UI', 11, 'bold'),
                             bg=colors['error'], fg=colors['button_text'],
                             relief='raised', bd=2, cursor='hand2')
        close_btn.pack(side='right', padx=(0, 10), ipady=8, ipadx=15)

    def start_manual_auth(self):
        """Startet manuelle Authentifizierung"""
        try:
            user_id = simpledialog.askstring(
                "🔧 Manuelle Authentifizierung",
                "Gib deine Discord User ID ein:\n\n"
                "💡 Wie finde ich meine User ID?\n"
                "1. Discord öffnen\n"
                "2. Benutzereinstellungen → Erweitert\n"
                "3. 'Entwicklermodus' aktivieren\n"
                "4. Rechtsklick auf deinen Namen → 'ID kopieren'",
                parent=self.root
            )
            
            if user_id:
                try:
                    user_id = int(user_id.strip())
                    self.authenticated_user_id = user_id
                    self.add_log(f"✅ Manuell authentifiziert als User ID: {user_id}")
                    self.update_auth_ui(f"User ID: {user_id}")
                except ValueError:
                    messagebox.showerror("Ungültige ID", "Die eingegebene User ID ist ungültig!")
                    
        except Exception as e:
            self.add_log(f"❌ Manuelle Authentifizierung Fehler: {e}")
            messagebox.showerror("Fehler", f"Fehler bei der Authentifizierung:\n\n{str(e)}")

    def update_auth_ui(self, username):
        """Aktualisiert die Authentifizierungs-UI mit verbesserter Sichtbarkeit"""
        colors = WINDOW_CONFIG['colors']
        
        if self.authenticated_user_id:
            self.auth_info.config(
                text=f"✅ Angemeldet als: {username}",
                fg=colors['success']
            )
            self.oauth_btn.config(state='disabled', bg=colors['text_disabled'])
            self.manual_btn.config(state='disabled', bg=colors['text_disabled'])
            self.logout_btn.config(state='normal', bg=colors['error'])
        else:
            self.auth_info.config(
                text="Nicht authentifiziert - Melde dich an um alle Features zu nutzen!",
                fg=colors['warning']
            )
            self.oauth_btn.config(state='normal', bg=colors['primary'])
            self.manual_btn.config(state='normal', bg=colors['warning'])
            self.logout_btn.config(state='disabled', bg=colors['text_disabled'])

    def logout_user(self):
        """Meldet den User ab"""
        result = messagebox.askyesno(
            "Abmelden", 
            "Möchtest du dich wirklich abmelden?\n\n"
            "Du verlierst den Zugriff auf authentifizierte Features.",
            parent=self.root
        )
        
        if result:
            self.authenticated_user_id = None
            self.add_log("👋 Erfolgreich abgemeldet")
            self.update_auth_ui("")

    def _add_tab_hover_effects(self):
        # Implementiere Hover-Effekte für Tab-Buttons
        pass 