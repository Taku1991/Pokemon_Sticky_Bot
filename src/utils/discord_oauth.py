"""
Discord OAuth2 Authentifizierung mit Flask
VERBESSERTE Version - Behebt Token Exchange 401 Fehler + AUTO SHUTDOWN
"""

import os
import threading
import time
import webbrowser
import logging
from flask import Flask, redirect, request, session, render_template_string, jsonify
import requests
from datetime import datetime, timedelta

# Flask App Setup
app = Flask(__name__)
app.secret_key = os.urandom(24)

# OAuth2 Konfiguration
CLIENT_ID = None
CLIENT_SECRET = None
REDIRECT_URI = 'http://localhost:5000/callback'
API_BASE = 'https://discord.com/api'
OAUTH_SCOPE = 'identify guilds'

# Globale Variablen
auth_result = None
server_thread = None
authenticated_user = None
server_shutdown_func = None

class DiscordOAuth:
    """Discord OAuth2 Authentifizierung Manager"""
    
    def __init__(self, client_id, client_secret=None):
        global CLIENT_ID, CLIENT_SECRET
        CLIENT_ID = client_id
        
        if client_secret:
            CLIENT_SECRET = client_secret
        else:
            CLIENT_SECRET = os.getenv('DISCORD_CLIENT_SECRET')
            if not CLIENT_SECRET:
                CLIENT_SECRET = client_id
        
        self.port = 5000
        self.timeout = 300  # 5 Minuten
        self.server_process = None
        
    def start_auth_flow(self):
        """Startet den OAuth2 Authentifizierungsflow"""
        global auth_result, server_thread, server_shutdown_func
        
        # Reset result
        auth_result = None
        server_shutdown_func = None
        
        # Prüfe Port-Verfügbarkeit
        if not self._check_port_available():
            return False, "Port 5000 ist bereits belegt. Bitte andere Anwendungen schließen."
        
        # Start Flask server in separate thread
        server_thread = threading.Thread(target=self._run_server, daemon=True)
        server_thread.start()
        
        # Warte kurz damit Server startet
        time.sleep(2)
        
        # Öffne Browser mit OAuth URL
        auth_url = f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope={OAUTH_SCOPE}"
        
        webbrowser.open(auth_url)
        
        # Warte auf Authentifizierung
        start_time = time.time()
        while auth_result is None and (time.time() - start_time) < self.timeout:
            time.sleep(1)
            
        # AUTO-SHUTDOWN nach OAuth Abschluss
        self._shutdown_server()
        
        if auth_result is None:
            logging.error("OAuth2 Authentifizierung Timeout")
            return False, "Authentifizierung Timeout (5 Minuten). Bitte versuche es erneut."
            
        if auth_result.get('success'):
            return True, auth_result.get('user_data')
        else:
            logging.error(f"OAuth2 Fehler: {auth_result.get('error')}")
            return False, auth_result.get('error', 'Unbekannter Fehler')
    
    def _shutdown_server(self):
        """Beendet den Flask Server automatisch"""
        try:
            if server_shutdown_func:
                server_shutdown_func()
            else:
                time.sleep(3)
                
        except Exception as e:
            logging.warning(f"OAuth Server Shutdown Warnung: {e}")
    
    def _check_port_available(self):
        """Prüft ob Port 5000 verfügbar ist"""
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', self.port))
                return True
        except OSError:
            return False
            
    def _run_server(self):
        """Startet Flask Server für OAuth Callback"""
        global server_shutdown_func
        
        try:
            from werkzeug.serving import make_server
            
            server = make_server('127.0.0.1', self.port, app, threaded=True)
            server_shutdown_func = server.shutdown
            
            server.serve_forever()
            
        except Exception as e:
            logging.error(f"Flask Server Fehler: {e}")
            global auth_result
            auth_result = {'success': False, 'error': f'Server Fehler: {str(e)}'}

# Flask Routes
@app.route('/')
def login():
    """Startet OAuth2 Flow"""
    auth_url = f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope={OAUTH_SCOPE}"
    return redirect(auth_url)

@app.route('/callback')
def callback():
    """OAuth2 Callback Handler"""
    global auth_result
    
    try:
        code = request.args.get('code')
        error = request.args.get('error')
        
        if error:
            logging.error(f"Discord OAuth2 Error: {error}")
            auth_result = {'success': False, 'error': f'Discord OAuth Fehler: {error}'}
            return render_error_page(f"Discord OAuth Fehler: {error}")
            
        if not code:
            logging.error("Kein Authorization Code erhalten")
            auth_result = {'success': False, 'error': 'Kein Authorization Code'}
            return render_error_page("Kein Authorization Code erhalten")
            
        # Token Exchange
        token_data = {
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': REDIRECT_URI,
            'scope': OAUTH_SCOPE
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'StickyBot-Discord-OAuth/1.0'
        }
        
        token_response = requests.post(f"{API_BASE}/oauth2/token", data=token_data, headers=headers, timeout=30)
        
        if token_response.status_code != 200:
            error_detail = ""
            try:
                error_json = token_response.json()
                error_detail = f"\n\nDetails: {error_json.get('error_description', error_json.get('error', 'Unbekannt'))}"
            except:
                error_detail = f"\n\nHTTP Response: {token_response.text[:200]}"
            
            error_msg = f"Token Exchange fehlgeschlagen: {token_response.status_code}{error_detail}"
            logging.error(error_msg)
            
            if token_response.status_code == 401:
                error_msg = (
                    "Discord OAuth2 Authentifizierung fehlgeschlagen (401 Unauthorized).\n\n"
                    "🔧 Lösungsschritte:\n"
                    "1. Prüfe deine Discord Application im Developer Portal\n"
                    "2. Stelle sicher, dass der Bot Token korrekt ist\n"
                    "3. Prüfe OAuth2 Redirect URI: http://localhost:5000/callback\n"
                    "4. Verwende die korrekte Client-ID aus dem Developer Portal\n\n"
                    "💡 Alternative: Verwende den Challenge-Response Modus\n"
                    "   (Klicke 'Alternative Authentifizierung' in der GUI)"
                )
            
            auth_result = {'success': False, 'error': error_msg}
            return render_error_page(error_msg)
            
        token_info = token_response.json()
        access_token = token_info['access_token']
        
        # Get user info
        auth_headers = {
            'Authorization': f"Bearer {access_token}",
            'User-Agent': 'StickyBot-Discord-OAuth/1.0'
        }
        
        user_response = requests.get(f"{API_BASE}/users/@me", headers=auth_headers, timeout=30)
        if user_response.status_code != 200:
            error_msg = f"User Info Abruf fehlgeschlagen: {user_response.status_code}"
            logging.error(error_msg)
            auth_result = {'success': False, 'error': error_msg}
            return render_error_page(error_msg)
            
        user_data = user_response.json()
        
        # Get user guilds
        guilds_response = requests.get(f"{API_BASE}/users/@me/guilds", headers=auth_headers, timeout=30)
        if guilds_response.status_code != 200:
            error_msg = f"Server Info Abruf fehlgeschlagen: {guilds_response.status_code}"
            logging.error(error_msg)
            auth_result = {'success': False, 'error': error_msg}
            return render_error_page(error_msg)
            
        guilds = guilds_response.json()
        
        # Check permissions
        authorized_guilds = []
        bot_roles = load_bot_roles()
        user_id = str(user_data['id'])
        
        for guild in guilds:
            guild_id = str(guild['id'])
            
            if guild_id in bot_roles:
                roles_data = bot_roles[guild_id]
                admin_users = [str(admin) for admin in roles_data.get('admin', [])]
                editor_users = [str(ed) for ed in roles_data.get('editor', [])]
                
                is_admin = user_id in admin_users
                is_editor = user_id in editor_users
                
                if is_admin or is_editor:
                    authorized_guilds.append({
                        'id': guild['id'],
                        'name': guild['name'],
                        'role': 'Bot-Master' if is_admin else 'Editor'
                    })
        
        if not authorized_guilds:
            error_msg = (
                f"User {user_data['username']} ist auf keinem Bot-Server als Master/Editor registriert.\n\n"
                "🔧 Lösungsschritte:\n"
                "1. Verwende '/setup_botmaster' auf einem Discord-Server mit dem Bot\n"
                "2. Lass dich von einem bestehenden Bot-Master als Editor hinzufügen\n"
                "3. Stelle sicher, dass der Bot auf deinem Server aktiv ist\n\n"
                f"📊 Du bist auf {len(guilds)} Server(n), aber auf keinem als Bot-Master/Editor registriert."
            )
            logging.warning(error_msg)
            auth_result = {'success': False, 'error': error_msg}
            return render_error_page(error_msg)
            
        # Erfolgreiche Authentifizierung
        final_user_data = {
            'id': user_data['id'],
            'username': user_data['username'],
            'discriminator': user_data.get('discriminator', '0'),
            'avatar': user_data.get('avatar'),
            'authorized_guilds': authorized_guilds
        }
        
        auth_result = {'success': True, 'user_data': final_user_data}
        
        return render_success_page(final_user_data)
        
    except requests.exceptions.Timeout:
        error_msg = "Discord API Timeout - Bitte versuche es erneut"
        logging.error(error_msg)
        auth_result = {'success': False, 'error': error_msg}
        return render_error_page(error_msg)
        
    except requests.exceptions.ConnectionError:
        error_msg = "Keine Internetverbindung zu Discord API"
        logging.error(error_msg)
        auth_result = {'success': False, 'error': error_msg}
        return render_error_page(error_msg)
        
    except Exception as e:
        error_msg = f"Unerwarteter Fehler: {str(e)}"
        logging.error(error_msg, exc_info=True)
        auth_result = {'success': False, 'error': error_msg}
        return render_error_page(error_msg)

def load_bot_roles():
    """Lädt Bot-Rollen Konfiguration aus dem einheitlichen verschlüsselten Permission-System"""
    try:
        # METHODE 1: Direkt aus .env laden
        import os
        from src.utils.path_manager import get_application_path
        
        app_path = get_application_path()
        env_file = os.path.join(app_path, '.env')
        
        bot_token = None
        if os.path.exists(env_file):
            try:
                with open(env_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    for line in content.splitlines():
                        if line.strip().startswith('DISCORD_TOKEN='):
                            bot_token = line.split('=', 1)[1].strip()
                            bot_token = bot_token.strip('"').strip("'")
                            break
                            
                if not (bot_token and len(bot_token) > 20):
                    bot_token = None
                    
            except Exception:
                bot_token = None
        
        # METHODE 2: Fallback auf permissions.py Funktion
        if not bot_token:
            from src.utils.permissions import get_bot_token
            bot_token = get_bot_token()
        
        if not bot_token:
            return {}
        
        # Verschlüsselte Berechtigungen laden
        from src.utils.secure_storage import SecureStorage
        storage = SecureStorage(bot_token)
        
        bot_roles = storage.load_encrypted_json("data/bot_roles.json")
        
        if bot_roles:
            return bot_roles
        else:
            return {}
            
    except Exception as e:
        logging.error(f"OAuth load_bot_roles Fehler: {e}")
        return {}

def render_success_page(user_data):
    """Rendert Erfolgs-Seite mit AUTO-SHUTDOWN"""
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>✅ Discord Authentifizierung Erfolgreich</title>
    <meta charset="UTF-8">
    <style>
        body { 
            font-family: 'Segoe UI', sans-serif; 
            text-align: center; 
            padding: 50px; 
            background: linear-gradient(135deg, #5865F2, #57F287); 
            color: white; 
            margin: 0;
        }
        .container { 
            background: rgba(255, 255, 255, 0.95); 
            color: #2C2F33;
            padding: 40px; 
            border-radius: 15px; 
            display: inline-block;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            max-width: 600px;
        }
        .icon { font-size: 64px; margin-bottom: 20px; }
        h1 { color: #57F287; margin-bottom: 15px; }
        .user-info { 
            background: #f8f9fa; 
            padding: 20px; 
            border-radius: 10px; 
            margin: 20px 0;
            text-align: left;
        }
        .server-list {
            background: #e3f2fd;
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
        }
        .server-item {
            background: white;
            padding: 10px;
            margin: 5px 0;
            border-radius: 5px;
            border-left: 4px solid #5865F2;
        }
        .close-btn {
            background: #5865F2;
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            margin-top: 20px;
        }
        .auto-close {
            background: #FAA61A;
            color: white;
            padding: 10px 20px;
            border-radius: 8px;
            margin: 20px 0;
            border: 2px solid #E89C0D;
        }
        .countdown {
            font-weight: bold;
            color: #E89C0D;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">✅</div>
        <h1>Discord Authentifizierung Erfolgreich!</h1>
        
        <div class="user-info">
            <h3>🔐 Authentifiziert als:</h3>
            <p><strong>{{ user_data.username }}#{{ user_data.discriminator }}</strong></p>
            <p><strong>User-ID:</strong> {{ user_data.id }}</p>
            
            <div class="server-list">
                <h4>🏠 Berechtigte Server ({{ user_data.authorized_guilds|length }}):</h4>
                {% for guild in user_data.authorized_guilds %}
                <div class="server-item">
                    <strong>{{ guild.name }}</strong> - {{ guild.role }}
                </div>
                {% endfor %}
            </div>
        </div>
        
        <p><strong>🎉 Du hast jetzt Zugriff auf den StickyBot GUI!</strong></p>
        <p>Du kannst dieses Fenster schließen und zur StickyBot GUI zurückkehren.</p>
        
        <div class="auto-close">
            🔄 OAuth-Server wird automatisch in <span class="countdown" id="countdown">10</span> Sekunden beendet<br>
            <small>Port 5000 wird freigegeben für weitere OAuth-Versuche</small>
        </div>
        
        <button class="close-btn" onclick="closeWindow()">Fenster jetzt schließen</button>
        <button class="close-btn" onclick="goToStickyBot()" style="background: #57F287; margin-left: 10px;">🤖 Zurück zum StickyBot GUI</button>
    </div>
    
    <script>
        let countdown = 10;
        const countdownEl = document.getElementById('countdown');
        
        const timer = setInterval(() => {
            countdown--;
            countdownEl.textContent = countdown;
            
            if (countdown <= 0) {
                clearInterval(timer);
                countdownEl.parentElement.innerHTML = '✅ OAuth-Server beendet - Port 5000 ist jetzt frei!';
                // Fenster schließen nach weiteren 2 Sekunden
                setTimeout(() => {
                    closeWindow();
                }, 2000);
            }
        }, 1000);
        
        // Verbesserte Fenster-Schließ-Funktion
        function closeWindow() {
            // Mehrere Methoden versuchen
            try {
                // Methode 1: Normales window.close()
                window.close();
            } catch(e) {
                console.log('window.close() blockiert:', e);
            }
            
            // Methode 2: Browser-History zurück
            setTimeout(() => {
                try {
                    window.history.back();
                } catch(e) {
                    console.log('history.back() fehlgeschlagen:', e);
                }
            }, 500);
            
            // Methode 3: Tab schließen über Browser-API
            setTimeout(() => {
                try {
                    window.open('', '_self', '');
                    window.close();
                } catch(e) {
                    console.log('Alternative close() fehlgeschlagen:', e);
                }
            }, 1000);
            
            // Methode 4: User-Anweisung anzeigen
            setTimeout(() => {
                alert('✅ OAuth erfolgreich! Du kannst diesen Tab jetzt manuell schließen (Strg+W oder Tab-X).');
            }, 1500);
        }
        
        // Zurück zum StickyBot GUI
        function goToStickyBot() {
            // Versuche das Hauptfenster zu fokussieren
            try {
                if (window.opener && !window.opener.closed) {
                    window.opener.focus();
                    window.close();
                } else {
                    alert('✅ OAuth erfolgreich! Wechsle zurück zum StickyBot GUI-Fenster.');
                }
            } catch(e) {
                alert('✅ OAuth erfolgreich! Wechsle zurück zum StickyBot GUI-Fenster.');
            }
        }
        
        // Cleanup bei manuellem Fensterschließen
        window.addEventListener('beforeunload', () => {
            clearInterval(timer);
        });
        
        // Keyboard Shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' || (e.ctrlKey && e.key === 'w')) {
                closeWindow();
            }
        });
    </script>
</body>
</html>
    """
    
    from jinja2 import Template
    template = Template(html)
    return template.render(user_data=user_data)

def render_error_page(error_message):
    """Rendert Fehler-Seite mit AUTO-SHUTDOWN"""
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>❌ Discord Authentifizierung Fehlgeschlagen</title>
    <meta charset="UTF-8">
    <style>
        body {{ 
            font-family: 'Segoe UI', sans-serif; 
            text-align: center; 
            padding: 50px; 
            background: linear-gradient(135deg, #ED4245, #FFA500); 
            color: white; 
            margin: 0;
        }}
        .container {{ 
            background: rgba(255, 255, 255, 0.95); 
            color: #2C2F33;
            padding: 40px; 
            border-radius: 15px; 
            display: inline-block;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            max-width: 600px;
        }}
        .icon {{ font-size: 64px; margin-bottom: 20px; }}
        h1 {{ color: #ED4245; margin-bottom: 15px; }}
        .error {{ 
            background: #FFF2F2; 
            border: 2px solid #FFB3B3; 
            padding: 20px; 
            border-radius: 8px; 
            margin: 20px 0;
            max-height: 200px;
            overflow-y: auto;
            text-align: left;
        }}
        .retry-btn {{
            background: #FAA61A;
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            margin: 10px;
        }}
        .auto-close {{
            background: #FFE5E5;
            color: #D63031;
            padding: 10px 20px;
            border-radius: 8px;
            margin: 20px 0;
            border: 2px solid #FFB3B3;
        }}
        .countdown {{
            font-weight: bold;
            color: #D63031;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">❌</div>
        <h1>Discord Authentifizierung Fehlgeschlagen</h1>
        
        <div class="error">
            <h3>Fehler:</h3>
            <p>{error_message}</p>
        </div>
        
        <h3>💡 Mögliche Lösungen:</h3>
        <ul style="text-align: left;">
            <li>Stelle sicher, dass du Bot-Master oder Editor auf einem Server bist</li>
            <li>Verwende '/setup_botmaster' auf Discord um Bot-Master zu werden</li>
            <li>Prüfe ob der Bot auf deinem Server aktiv ist</li>
            <li>Versuche es nochmal oder verwende 'Manuelle Authentifizierung'</li>
        </ul>
        
        <div class="auto-close">
            🔄 OAuth-Server wird automatisch in <span class="countdown" id="countdown">15</span> Sekunden beendet<br>
            <small>Port 5000 wird freigegeben für weitere Versuche</small>
        </div>
        
        <button class="retry-btn" onclick="window.location.href='/'">🔄 Erneut versuchen</button>
        <button class="retry-btn" onclick="closeWindow()">❌ Fenster schließen</button>
    </div>
    
    <script>
        let countdown = 15;
        const countdownEl = document.getElementById('countdown');
        
        const timer = setInterval(() => {{
            countdown--;
            countdownEl.textContent = countdown;
            
            if (countdown <= 0) {{
                clearInterval(timer);
                countdownEl.parentElement.innerHTML = '✅ OAuth-Server beendet - Port 5000 ist jetzt frei!';
                // Fenster schließen nach weiteren 2 Sekunden
                setTimeout(() => {{
                    closeWindow();
                }}, 2000);
            }}
        }}, 1000);
        
        // Verbesserte Fenster-Schließ-Funktion
        function closeWindow() {{
            // Mehrere Methoden versuchen
            try {{
                // Methode 1: Normales window.close()
                window.close();
            }} catch(e) {{
                console.log('window.close() blockiert:', e);
            }}
            
            // Methode 2: Browser-History zurück
            setTimeout(() => {{
                try {{
                    window.history.back();
                }} catch(e) {{
                    console.log('history.back() fehlgeschlagen:', e);
                }}
            }}, 500);
            
            // Methode 3: Tab schließen über Browser-API
            setTimeout(() => {{
                try {{
                    window.open('', '_self', '');
                    window.close();
                }} catch(e) {{
                    console.log('Alternative close() fehlgeschlagen:', e);
                }}
            }}, 1000);
            
            // Methode 4: User-Anweisung anzeigen
            setTimeout(() => {{
                alert('Du kannst diesen Tab jetzt manuell schließen (Strg+W oder Tab-X).');
            }}, 1500);
        }}
        
        // Cleanup bei manuellem Fensterschließen
        window.addEventListener('beforeunload', () => {{
            clearInterval(timer);
        }});
        
        // Keyboard Shortcuts
        document.addEventListener('keydown', (e) => {{
            if (e.key === 'Escape' || (e.ctrlKey && e.key === 'w')) {{
                closeWindow();
            }}
        }});
    </script>
</body>
</html>
    """
    return html

@app.route('/status')
def status():
    """Status Endpoint"""
    return jsonify({
        'status': 'running',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/shutdown')
def shutdown_endpoint():
    """Manueller Shutdown Endpoint"""
    global server_shutdown_func
    
    try:
        if server_shutdown_func:
            # Shutdown in separatem Thread um Response zu senden
            def delayed_shutdown():
                time.sleep(1)  # Kurz warten damit Response gesendet wird
                server_shutdown_func()
                
            shutdown_thread = threading.Thread(target=delayed_shutdown, daemon=True)
            shutdown_thread.start()
            
            return jsonify({
                'status': 'shutting_down',
                'message': 'OAuth-Server wird beendet...',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Shutdown-Funktion nicht verfügbar',
                'timestamp': datetime.now().isoformat()
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Shutdown Fehler: {str(e)}',
            'timestamp': datetime.now().isoformat()
        })

def test_oauth():
    """Test-Funktion"""
    logging.info("🧪 Discord OAuth2 Test")
    logging.info("Stelle sicher, dass CLIENT_ID konfiguriert ist")

if __name__ == "__main__":
    test_oauth() 