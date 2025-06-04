"""
Discord Bot Token Setup Utility
Behandelt das sichere Setup und die Verwaltung von Discord Bot Tokens
"""
import os
import tkinter as tk
from tkinter import messagebox, simpledialog
import logging
import webbrowser
from src.utils.path_manager import get_application_path
from src.utils.logging_setup import safe_print


def setup_token():
    """Führt das Token-Setup durch"""
    try:
        safe_print("🔑 Discord Bot Token Setup wird gestartet...")
        
        # Prüfe ob GUI verfügbar ist
        has_gui = True
        try:
            # Teste ob tkinter verfügbar ist
            test_root = tk.Tk()
            test_root.withdraw()
            test_root.destroy()
        except:
            has_gui = False
        
        if has_gui:
            return setup_token_gui()
        else:
            return setup_token_console()
            
    except Exception as e:
        logging.error(f"❌ Token Setup Fehler: {e}")
        safe_print(f"❌ Token Setup Fehler: {e}")
        return False


def setup_token_gui():
    """Token Setup mit GUI - Erweitert mit Client ID und OAuth"""
    try:
        safe_print("🖥️ GUI Token Setup wird gestartet...")
        
        # Setup Dialog erstellen
        setup_window = tk.Tk()
        setup_window.title("🔑 Discord Bot Setup")
        setup_window.geometry("650x900")
        setup_window.resizable(False, False)
        setup_window.configure(bg='#2C2F33')
        
        # Zentrieren
        setup_window.eval('tk::PlaceWindow . center')
        
        # Icon versuchen zu setzen
        try:
            setup_window.iconbitmap('icon.ico')
        except:
            pass
        
        # Header
        header_frame = tk.Frame(setup_window, bg='#5865F2', relief='flat')
        header_frame.pack(fill='x', pady=(0, 20))
        
        header_label = tk.Label(header_frame, 
                               text="🔑 Discord Bot Setup", 
                               font=('Segoe UI', 18, 'bold'),
                               fg='white', bg='#5865F2')
        header_label.pack(pady=20)
        
        # Main Frame mit Scrollbar
        canvas = tk.Canvas(setup_window, bg='#2C2F33')
        scrollbar = tk.Scrollbar(setup_window, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#2C2F33')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        main_frame = tk.Frame(scrollable_frame, bg='#2C2F33')
        main_frame.pack(fill='both', expand=True, padx=20)
        
        # Anleitung
        instruction_text = (
            "Willkommen beim erweiterten Sticky-Bot Setup!\n\n"
            "Für die volle Funktionalität (inklusive Discord OAuth Authentifizierung)\n"
            "benötigst du folgende Informationen:\n\n"
            "🔧 WO FINDE ICH DIESE INFORMATIONEN?\n"
            "1️⃣ Gehe zu: https://discord.com/developers/applications\n"
            "2️⃣ Wähle deine Bot-Anwendung aus (oder erstelle eine neue)\n"
            "3️⃣ Auf der 'General Information' Seite findest du:\n"
            "   • Application ID (= Client ID)\n"
            "   • Client Secret (ggf. 'Generate New Secret' klicken)\n"
            "4️⃣ Im 'Bot' Tab findest du:\n"
            "   • Bot Token (ggf. 'Reset Token' klicken)\n\n"
            "⚠️ WICHTIG: Teile diese Informationen NIEMALS mit anderen!"
        )
        
        instruction_label = tk.Label(main_frame, text=instruction_text,
                                    font=('Segoe UI', 11),
                                    fg='#DCDDDE', bg='#2C2F33',
                                    justify='left', wraplength=600)
        instruction_label.pack(pady=(0, 20))
        
        # Developer Portal Button
        def open_discord_dev():
            webbrowser.open('https://discord.com/developers/applications')
        
        dev_btn = tk.Button(main_frame, text="🌐 Discord Developer Portal öffnen",
                           command=open_discord_dev,
                           font=('Segoe UI', 12, 'bold'),
                           bg='#5865F2', fg='white',
                           relief='flat', cursor='hand2')
        dev_btn.pack(pady=(0, 30), ipady=10, ipadx=20)
        
        # --- CLIENT ID SECTION ---
        client_id_frame = tk.LabelFrame(main_frame, text="🆔 Application ID (Client ID)", 
                                       font=('Segoe UI', 12, 'bold'),
                                       fg='#DCDDDE', bg='#2C2F33')
        client_id_frame.pack(fill='x', pady=(0, 15), padx=10, ipady=10)
        
        client_id_info = tk.Label(client_id_frame, 
                                 text="Die Application ID findest du unter 'General Information'.\n"
                                      "Erforderlich für Discord OAuth Authentifizierung.",
                                 font=('Segoe UI', 9),
                                 fg='#B9BBBE', bg='#2C2F33')
        client_id_info.pack(pady=(0, 5))
        
        client_id_entry = tk.Entry(client_id_frame, font=('Segoe UI', 11),
                                  bg='#40444B', fg='#DCDDDE',
                                  insertbackground='#FFFFFF', width=60)
        client_id_entry.pack(fill='x', ipady=8, padx=10, pady=(0, 10))
        
        # --- CLIENT SECRET SECTION ---
        client_secret_frame = tk.LabelFrame(main_frame, text="🔐 Client Secret", 
                                           font=('Segoe UI', 12, 'bold'),
                                           fg='#DCDDDE', bg='#2C2F33')
        client_secret_frame.pack(fill='x', pady=(0, 15), padx=10, ipady=10)
        
        client_secret_info = tk.Label(client_secret_frame, 
                                     text="Der Client Secret findet sich unter 'General Information'.\n"
                                          "Falls nicht vorhanden: 'Generate New Secret' klicken.\n"
                                          "Optional: Nur für erweiterte OAuth Features benötigt.",
                                     font=('Segoe UI', 9),
                                     fg='#B9BBBE', bg='#2C2F33')
        client_secret_info.pack(pady=(0, 5))
        
        client_secret_entry = tk.Entry(client_secret_frame, font=('Segoe UI', 11),
                                      bg='#40444B', fg='#DCDDDE',
                                      insertbackground='#FFFFFF',
                                      show='*', width=60)
        client_secret_entry.pack(fill='x', ipady=8, padx=10, pady=(0, 5))
        
        # Client Secret anzeigen/verstecken
        show_client_secret = tk.BooleanVar()
        
        def toggle_client_secret_visibility():
            if show_client_secret.get():
                client_secret_entry.config(show='')
            else:
                client_secret_entry.config(show='*')
        
        show_secret_check = tk.Checkbutton(client_secret_frame, text="Client Secret anzeigen",
                                          variable=show_client_secret,
                                          command=toggle_client_secret_visibility,
                                          font=('Segoe UI', 9),
                                          fg='#B9BBBE', bg='#2C2F33',
                                          selectcolor='#40444B')
        show_secret_check.pack(anchor='w', padx=10, pady=(0, 10))
        
        # --- BOT TOKEN SECTION ---
        token_frame = tk.LabelFrame(main_frame, text="🤖 Bot Token", 
                                   font=('Segoe UI', 12, 'bold'),
                                   fg='#DCDDDE', bg='#2C2F33')
        token_frame.pack(fill='x', pady=(0, 15), padx=10, ipady=10)
        
        token_info = tk.Label(token_frame, 
                             text="Der Bot Token findest du im 'Bot' Tab deiner Anwendung.\n"
                                  "ERFORDERLICH: Ohne Token kann der Bot nicht starten!",
                             font=('Segoe UI', 9),
                             fg='#B9BBBE', bg='#2C2F33')
        token_info.pack(pady=(0, 5))
        
        token_entry = tk.Entry(token_frame, font=('Segoe UI', 11),
                              bg='#40444B', fg='#DCDDDE',
                              insertbackground='#FFFFFF',
                              show='*', width=60)
        token_entry.pack(fill='x', ipady=8, padx=10, pady=(0, 5))
        
        # Token anzeigen/verstecken
        show_token = tk.BooleanVar()
        
        def toggle_token_visibility():
            if show_token.get():
                token_entry.config(show='')
            else:
                token_entry.config(show='*')
        
        show_token_check = tk.Checkbutton(token_frame, text="Bot Token anzeigen",
                                         variable=show_token,
                                         command=toggle_token_visibility,
                                         font=('Segoe UI', 9),
                                         fg='#B9BBBE', bg='#2C2F33',
                                         selectcolor='#40444B')
        show_token_check.pack(anchor='w', padx=10, pady=(0, 10))
        
        # --- OAUTH SECTION ---
        oauth_frame = tk.LabelFrame(main_frame, text="🔐 OAuth Authentifizierung", 
                                   font=('Segoe UI', 12, 'bold'),
                                   fg='#DCDDDE', bg='#2C2F33')
        oauth_frame.pack(fill='x', pady=(0, 20), padx=10, ipady=10)
        
        oauth_info = tk.Label(oauth_frame, 
                             text="Nach dem Speichern kannst du dich über Discord OAuth authentifizieren.\n"
                                  "Das ermöglicht sichere Berechtigung ohne User-ID eingeben zu müssen!",
                             font=('Segoe UI', 9),
                             fg='#B9BBBE', bg='#2C2F33')
        oauth_info.pack(pady=(0, 10))
        
        def test_oauth():
            """Testet die OAuth Konfiguration"""
            client_id = client_id_entry.get().strip()
            client_secret = client_secret_entry.get().strip()
            
            if not client_id:
                messagebox.showwarning("Fehlende Client ID", 
                                     "Bitte gib zuerst eine Client ID ein!")
                return
            
            # Speichere temporär die Werte
            try:
                # OAuth Test Dialog
                test_window = tk.Toplevel(setup_window)
                test_window.title("🔐 OAuth Test")
                test_window.geometry("400x300")
                test_window.configure(bg='#2C2F33')
                test_window.grab_set()
                
                info_label = tk.Label(test_window, 
                                     text="🔄 Discord OAuth Test wird gestartet...\n\n"
                                          "1. Browser wird geöffnet\n"
                                          "2. Bei Discord einloggen\n"
                                          "3. Bot autorisieren\n"
                                          "4. Zurück zu diesem Fenster",
                                     font=('Segoe UI', 12),
                                     fg='#DCDDDE', bg='#2C2F33',
                                     justify='center')
                info_label.pack(expand=True)
                
                def run_oauth_test():
                    try:
                        from src.utils.discord_oauth import DiscordOAuth
                        oauth = DiscordOAuth(client_id, client_secret)
                        success, result = oauth.start_auth_flow()
                        
                        test_window.destroy()
                        
                        if success:
                            user_info = result
                            messagebox.showinfo("✅ OAuth Test erfolgreich!",
                                              f"Authentifizierung erfolgreich!\n\n"
                                              f"Benutzer: {user_info.get('username', 'Unbekannt')}\n"
                                              f"ID: {user_info.get('id', 'Unbekannt')}\n\n"
                                              f"OAuth Konfiguration funktioniert!")
                        else:
                            messagebox.showerror("❌ OAuth Test fehlgeschlagen",
                                               f"OAuth Test fehlgeschlagen:\n\n{result}")
                    except Exception as e:
                        test_window.destroy()
                        messagebox.showerror("❌ OAuth Fehler",
                                           f"OAuth Test Fehler:\n\n{str(e)}")
                
                # Test nach kurzer Verzögerung starten
                test_window.after(2000, run_oauth_test)
                
            except Exception as e:
                messagebox.showerror("OAuth Test Fehler", f"Fehler beim OAuth Test:\n{str(e)}")
        
        oauth_test_btn = tk.Button(oauth_frame, text="🧪 OAuth Test",
                                  command=test_oauth,
                                  font=('Segoe UI', 11, 'bold'),
                                  bg='#FAA61A', fg='white',
                                  relief='flat', cursor='hand2')
        oauth_test_btn.pack(pady=(0, 10), ipady=8, ipadx=15)
        
        # Status Label
        status_label = tk.Label(main_frame, text="",
                               font=('Segoe UI', 10),
                               fg='#FAA61A', bg='#2C2F33')
        status_label.pack(pady=(0, 10))
        
        # Button Frame
        button_frame = tk.Frame(main_frame, bg='#2C2F33')
        button_frame.pack(fill='x', pady=(0, 30))
        
        # Validation Result
        validation_result = {'valid': False}
        
        def validate_inputs():
            """Validiert alle Eingaben"""
            token = token_entry.get().strip()
            client_id = client_id_entry.get().strip()
            client_secret = client_secret_entry.get().strip()
            
            if not token:
                status_label.config(text="❌ Bot Token ist erforderlich!", fg='#ed4245')
                return False
            
            # Basic Token Format Validation
            if len(token) < 50:
                status_label.config(text="❌ Bot Token zu kurz! Überprüfe deine Eingabe.", fg='#ed4245')
                return False
            
            # Discord Bot Token Pattern (vereinfacht)
            if not (token.count('.') >= 2 or token.startswith('MT')):
                status_label.config(text="❌ Bot Token-Format ungültig!", fg='#ed4245')
                return False
            
            # Client ID validation (optional aber empfohlen)
            if client_id and len(client_id) < 17:
                status_label.config(text="❌ Client ID zu kurz! Sollte mindestens 17 Zeichen haben.", fg='#ed4245')
                return False
            
            status_label.config(text="✅ Alle Eingaben scheinen korrekt zu sein!", fg='#00b894')
            validation_result['valid'] = True
            return True
        
        def save_configuration():
            """Speichert die komplette Konfiguration"""
            if not validate_inputs():
                return
            
            token = token_entry.get().strip()
            client_id = client_id_entry.get().strip()
            client_secret = client_secret_entry.get().strip()
            
            try:
                # .env Datei erstellen/aktualisieren
                app_path = get_application_path()
                env_path = os.path.join(app_path, '.env')
                
                # Bestehende .env lesen falls vorhanden
                env_content = {}
                if os.path.exists(env_path):
                    with open(env_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#') and '=' in line:
                                key, value = line.split('=', 1)
                                env_content[key.strip()] = value.strip()
                
                # Neue Werte hinzufügen/aktualisieren
                env_content['DISCORD_TOKEN'] = token
                if client_id:
                    env_content['DISCORD_CLIENT_ID'] = client_id
                if client_secret:
                    env_content['DISCORD_CLIENT_SECRET'] = client_secret
                
                # .env Datei schreiben
                with open(env_path, 'w', encoding='utf-8') as f:
                    f.write("# Sticky-Bot Konfiguration\n")
                    f.write("# WARNUNG: Diese Datei NIEMALS mit anderen teilen!\n\n")
                    f.write("# Bot Token (ERFORDERLICH)\n")
                    f.write(f"DISCORD_TOKEN={env_content['DISCORD_TOKEN']}\n\n")
                    
                    if 'DISCORD_CLIENT_ID' in env_content:
                        f.write("# Client ID für OAuth (Optional)\n")
                        f.write(f"DISCORD_CLIENT_ID={env_content['DISCORD_CLIENT_ID']}\n\n")
                    
                    if 'DISCORD_CLIENT_SECRET' in env_content:
                        f.write("# Client Secret für OAuth (Optional)\n")
                        f.write(f"DISCORD_CLIENT_SECRET={env_content['DISCORD_CLIENT_SECRET']}\n\n")
                    
                    # Andere Einstellungen beibehalten
                    for key, value in env_content.items():
                        if key not in ['DISCORD_TOKEN', 'DISCORD_CLIENT_ID', 'DISCORD_CLIENT_SECRET']:
                            f.write(f"{key}={value}\n")
                
                logging.info(f"✅ Konfiguration in .env gespeichert: {env_path}")
                
                # Erfolgsmeldung mit OAuth Info
                oauth_info = ""
                if client_id:
                    oauth_info = "\n\n🔐 OAuth Authentifizierung ist verfügbar!\nDu kannst dich jetzt sicher über Discord authentifizieren."
                
                messagebox.showinfo("✅ Setup erfolgreich!",
                                  f"Discord Bot Konfiguration wurde erfolgreich gespeichert!\n\n"
                                  f"Datei: {env_path}\n"
                                  f"Bot Token: ✅\n"
                                  f"Client ID: {'✅' if client_id else '❌'}\n"
                                  f"Client Secret: {'✅' if client_secret else '❌'}"
                                  f"{oauth_info}\n\n"
                                  f"Der Bot kann jetzt gestartet werden.",
                                  parent=setup_window)
                
                setup_window.destroy()
                return True
                
            except Exception as e:
                logging.error(f"❌ Fehler beim Speichern der Konfiguration: {e}")
                messagebox.showerror("Fehler",
                                   f"Fehler beim Speichern der Konfiguration:\n{str(e)}",
                                   parent=setup_window)
                return False
        
        def cancel_setup():
            """Bricht das Setup ab"""
            result = messagebox.askyesno("Setup abbrechen?",
                                       "Möchtest du das Setup wirklich abbrechen?\n"
                                       "Ohne Token kann der Bot nicht gestartet werden.",
                                       parent=setup_window)
            if result:
                setup_window.destroy()
                return False
        
        # Buttons
        cancel_btn = tk.Button(button_frame, text="❌ Abbrechen",
                              command=cancel_setup,
                              font=('Segoe UI', 12, 'bold'),
                              bg='#4F545C', fg='white',
                              relief='flat', cursor='hand2')
        cancel_btn.pack(side='left', ipady=10, ipadx=20)
        
        validate_btn = tk.Button(button_frame, text="🔍 Eingaben prüfen",
                                command=validate_inputs,
                                font=('Segoe UI', 12, 'bold'),
                                bg='#FAA61A', fg='white',
                                relief='flat', cursor='hand2')
        validate_btn.pack(side='left', padx=(10, 0), ipady=10, ipadx=20)
        
        save_btn = tk.Button(button_frame, text="💾 Speichern & Weiter",
                            command=save_configuration,
                            font=('Segoe UI', 12, 'bold'),
                            bg='#00b894', fg='white',
                            relief='flat', cursor='hand2')
        save_btn.pack(side='right', ipady=10, ipadx=20)
        
        # Enter Taste für Speichern
        def on_enter(event):
            save_configuration()
        
        token_entry.bind('<Return>', on_enter)
        token_entry.focus()
        
        # Canvas und Scrollbar konfigurieren
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Mouse wheel scrolling
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<MouseWheel>", on_mousewheel)
        
        # Fenster anzeigen
        setup_window.mainloop()
        
        return validation_result['valid']
        
    except Exception as e:
        logging.error(f"❌ GUI Token Setup Fehler: {e}")
        safe_print(f"❌ GUI Token Setup Fehler: {e}")
        return False


def setup_token_console():
    """Token Setup über Konsole (Fallback)"""
    try:
        safe_print("\n" + "="*60)
        safe_print("🔑 DISCORD BOT TOKEN SETUP")
        safe_print("="*60)
        safe_print()
        safe_print("Du benötigst einen Discord Bot Token, um den Bot zu betreiben.")
        safe_print()
        safe_print("📋 ANLEITUNG:")
        safe_print("1. Gehe zu: https://discord.com/developers/applications")
        safe_print("2. Klicke auf 'New Application' oder wähle eine bestehende aus")
        safe_print("3. Gehe zum 'Bot' Tab auf der linken Seite")
        safe_print("4. Kopiere den 'Token' (falls nicht sichtbar: 'Reset Token')")
        safe_print("5. Füge den Token hier ein")
        safe_print()
        safe_print("⚠️  WICHTIG: Teile deinen Token NIEMALS mit anderen!")
        safe_print("="*60)
        safe_print()
        
        while True:
            token = input("🔑 Discord Bot Token eingeben: ").strip()
            
            if not token:
                safe_print("❌ Bitte gib einen Token ein!")
                continue
            
            # Basic Validation
            if len(token) < 50:
                safe_print("❌ Token zu kurz! Überprüfe deine Eingabe.")
                continue
            
            if not (token.count('.') >= 2 or token.startswith('MT')):
                safe_print("❌ Token-Format ungültig! Überprüfe deine Eingabe.")
                continue
            
            safe_print("✅ Token-Format scheint korrekt zu sein!")
            
            # Bestätigung
            confirm = input("\n💾 Token speichern? (j/n): ").lower().strip()
            
            if confirm in ['j', 'ja', 'y', 'yes']:
                # .env Datei erstellen
                app_path = get_application_path()
                env_path = os.path.join(app_path, '.env')
                
                try:
                    # Bestehende .env lesen falls vorhanden
                    env_content = {}
                    if os.path.exists(env_path):
                        with open(env_path, 'r', encoding='utf-8') as f:
                            for line in f:
                                line = line.strip()
                                if line and not line.startswith('#') and '=' in line:
                                    key, value = line.split('=', 1)
                                    env_content[key.strip()] = value.strip()
                    
                    # Token hinzufügen
                    env_content['DISCORD_TOKEN'] = token
                    
                    # .env Datei schreiben
                    with open(env_path, 'w', encoding='utf-8') as f:
                        f.write("# Sticky-Bot Konfiguration\n")
                        f.write("# WARNUNG: Diese Datei NIEMALS mit anderen teilen!\n\n")
                        for key, value in env_content.items():
                            f.write(f"{key}={value}\n")
                    
                    safe_print(f"✅ Token erfolgreich gespeichert: {env_path}")
                    safe_print("🚀 Der Bot kann jetzt gestartet werden!")
                    logging.info(f"✅ Token über Konsole gespeichert: {env_path}")
                    return True
                    
                except Exception as e:
                    safe_print(f"❌ Fehler beim Speichern: {e}")
                    logging.error(f"❌ Console Token Setup Speicher-Fehler: {e}")
                    return False
            else:
                safe_print("Setup abgebrochen.")
                return False
        
    except KeyboardInterrupt:
        safe_print("\n\n❌ Setup vom Benutzer abgebrochen.")
        return False
    except Exception as e:
        safe_print(f"❌ Console Token Setup Fehler: {e}")
        logging.error(f"❌ Console Token Setup Fehler: {e}")
        return False


def validate_existing_token():
    """Validiert den existierenden Token"""
    try:
        app_path = get_application_path()
        env_path = os.path.join(app_path, '.env')
        
        if not os.path.exists(env_path):
            return False, "Keine .env Datei gefunden"
        
        # .env Datei lesen
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('DISCORD_TOKEN='):
                    token = line.split('=', 1)[1].strip()
                    
                    # Basic Validation
                    if len(token) < 50:
                        return False, "Token zu kurz"
                    
                    if not (token.count('.') >= 2 or token.startswith('MT')):
                        return False, "Token-Format ungültig"
                    
                    return True, "Token ist gültig"
        
        return False, "Kein DISCORD_TOKEN in .env gefunden"
        
    except Exception as e:
        logging.error(f"❌ Token Validierung Fehler: {e}")
        return False, str(e)


def reset_token():
    """Startet das Token-Setup neu"""
    try:
        app_path = get_application_path()
        env_path = os.path.join(app_path, '.env')
        
        # Backup erstellen falls .env existiert
        if os.path.exists(env_path):
            backup_path = env_path + '.backup'
            os.rename(env_path, backup_path)
            logging.info(f"Backup erstellt: {backup_path}")
        
        # Neues Setup starten
        return setup_token()
        
    except Exception as e:
        logging.error(f"❌ Token Reset Fehler: {e}")
        return False


def get_token_info():
    """Gibt Informationen über den aktuellen Token zurück"""
    try:
        app_path = get_application_path()
        env_path = os.path.join(app_path, '.env')
        
        if not os.path.exists(env_path):
            return {
                'exists': False,
                'path': env_path,
                'status': 'Keine .env Datei gefunden'
            }
        
        # Token lesen
        with open(env_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'DISCORD_TOKEN=' in content:
            for line in content.split('\n'):
                if line.strip().startswith('DISCORD_TOKEN='):
                    token = line.split('=', 1)[1].strip()
                    
                    # Teilweise zensierter Token für Anzeige
                    if len(token) > 20:
                        censored = token[:8] + '...' + token[-4:]
                    else:
                        censored = token[:4] + '...'
                    
                    return {
                        'exists': True,
                        'path': env_path,
                        'status': 'Token konfiguriert',
                        'censored_token': censored,
                        'token_length': len(token)
                    }
        
        return {
            'exists': True,
            'path': env_path,
            'status': 'Datei existiert, aber kein Token gefunden'
        }
        
    except Exception as e:
        logging.error(f"❌ Token Info Fehler: {e}")
        return {
            'exists': False,
            'path': 'Unbekannt',
            'status': f'Fehler: {str(e)}'
        } 