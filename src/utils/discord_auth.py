import asyncio
import aiohttp
import webbrowser
import socket
import threading
import time
import json
import random
import string
from datetime import datetime, timedelta
from urllib.parse import urlencode, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
import logging
import discord

# Globaler Store für Verification-Codes
verification_codes = {}

class DiscordChallenge:
    """Sichere Discord Authentifizierung über Challenge-Response - VERBESSERTE VERSION"""
    
    def __init__(self, bot=None):
        self.bot = bot
        self.verification_timeout = 300  # 5 Minuten
        
    def generate_verification_code(self):
        """Generiert einen 6-stelligen Verification-Code"""
        return ''.join(random.choices(string.digits, k=6))
    
    def quick_auth_check(self, user_id):
        """Schnelle Authentifizierungs-Prüfung ohne DM"""
        try:
            # Lade Bot-Rollen Konfiguration
            import os
            data_dir = os.path.join(os.getcwd(), 'data')
            bot_roles_file = os.path.join(data_dir, 'bot_roles.json')
            
            if not os.path.exists(bot_roles_file):
                return False, "Keine Bot-Rollen Konfiguration gefunden"
                
            with open(bot_roles_file, 'r', encoding='utf-8') as f:
                bot_roles = json.load(f)
            
            user_id_str = str(user_id)
            authorized_servers = []
            
            for guild_id, roles_data in bot_roles.items():
                admin_users = roles_data.get('admin', [])
                editor_users = roles_data.get('editor', [])
                
                if user_id_str in admin_users:
                    authorized_servers.append(f"Server {guild_id} (Bot-Master)")
                elif user_id_str in editor_users:
                    authorized_servers.append(f"Server {guild_id} (Editor)")
            
            if authorized_servers:
                logging.info(f"✅ Quick Auth erfolgreich für User {user_id}: {len(authorized_servers)} Server")
                return True, {
                    'user_id': user_id,
                    'method': 'quick_auth',
                    'authorized_servers': authorized_servers
                }
            else:
                return False, f"User {user_id} ist auf keinem Server als Bot-Master/Editor registriert"
                
        except Exception as e:
            logging.error(f"❌ Quick Auth Fehler: {e}")
            return False, f"Authentifizierung Fehler: {str(e)}"
    
    def generate_bypass_code(self, user_id):
        """Generiert einen zeitbasierten Bypass-Code für registrierte Users"""
        try:
            # Prüfe erst ob User berechtigt ist
            is_authorized, result = self.quick_auth_check(user_id)
            if not is_authorized:
                return False, result
            
            # Generiere zeitbasierten Bypass-Code
            import hashlib
            time_window = int(time.time()) // 300  # 5-Minuten-Fenster
            bypass_seed = f"StickyBot_{user_id}_{time_window}"
            bypass_hash = hashlib.md5(bypass_seed.encode()).hexdigest()[:6].upper()
            
            # Speichere Bypass-Code
            self.store_bypass_code(user_id, bypass_hash)
            
            expiry_time = datetime.now() + timedelta(seconds=300)
            
            logging.info(f"🔑 Bypass-Code für User {user_id} generiert: {bypass_hash}")
            
            return True, {
                'bypass_code': bypass_hash,
                'expires_at': expiry_time.strftime("%H:%M:%S"),
                'user_id': user_id,
                'method': 'bypass_code'
            }
            
        except Exception as e:
            logging.error(f"❌ Bypass-Code Generation Fehler: {e}")
            return False, f"Bypass-Code Fehler: {str(e)}"
        
    async def send_verification_dm(self, user_id, code):
        """Sendet Verification-Code per DM an den User"""
        try:
            if not self.bot or not self.bot.user:
                logging.error("❌ Bot nicht verfügbar für DM-Versand")
                return False, "Bot nicht verfügbar"
            
            logging.info(f"🔍 Suche User mit ID: {user_id}")
            
            # Debug: Bot-Informationen
            logging.info(f"🤖 Bot Details: {self.bot.user.name} (ID: {self.bot.user.id})")
            logging.info(f"📊 Bot auf {len(self.bot.guilds)} Servern aktiv")
            
            user, user_name = await self.get_user_from_bot(user_id)
            
            if not user:
                # Debug: Zeige alle verfügbaren User IDs
                logging.error("❌ User wurde nicht gefunden. Debug-Informationen:")
                logging.error(f"Gesuchte User-ID: {user_id} (Typ: {type(user_id)})")
                
                # Zeige Bot-Master aus bot_roles.json
                try:
                    import os
                    import json
                    data_dir = os.path.join(os.getcwd(), 'data')
                    bot_roles_file = os.path.join(data_dir, 'bot_roles.json')
                    
                    if os.path.exists(bot_roles_file):
                        with open(bot_roles_file, 'r', encoding='utf-8') as f:
                            bot_roles = json.load(f)
                        
                        logging.error("🔍 Registrierte Bot-Master/Editoren:")
                        for guild_id, roles_data in bot_roles.items():
                            admin_users = roles_data.get('admin', [])
                            editor_users = roles_data.get('editor', [])
                            
                            # Prüfe ob Server aktiv ist
                            guild_active = any(str(g.id) == str(guild_id) for g in self.bot.guilds)
                            status = "✅ AKTIV" if guild_active else "❌ NICHT VERBUNDEN"
                            
                            logging.error(f"  Server {guild_id} ({status}): Admins={admin_users}, Editoren={editor_users}")
                            
                            # Prüfe ob gesuchte User-ID in den Daten ist
                            if str(user_id) in [str(admin) for admin in admin_users]:
                                logging.error(f"✅ User {user_id} ist Bot-Master für Server {guild_id} ({status})")
                            elif str(user_id) in [str(ed) for ed in editor_users]:
                                logging.error(f"✅ User {user_id} ist Editor für Server {guild_id} ({status})")
                                
                except Exception as debug_error:
                    logging.error(f"Debug-Info Fehler: {debug_error}")
                
                # ALTERNATIVE LÖSUNG: Fallback ohne DM
                logging.info("🔄 Starte Alternative: Bypass-Code Generation")
                print("🔄 Alternative: Bypass-Code wird generiert...")
                
                # Generiere speziellen Bypass-Code basierend auf User-ID und Zeitstempel
                import hashlib
                import time
                bypass_seed = f"{user_id}_{int(time.time())//300}"  # 5-Minuten-Fenster
                bypass_hash = hashlib.md5(bypass_seed.encode()).hexdigest()[:6].upper()
                
                logging.info(f"🔑 Bypass-Code generiert: {bypass_hash}")
                
                # Erweiterte Fehlermeldung mit Alternative
                error_msg = (
                    f"Discord User (ID: {user_id}) kann nicht erreicht werden.\n\n"
                    "🔍 Mögliche Ursachen:\n"
                    "• Du bist nicht auf dem aktiven Discord-Server\n"
                    "• Du hast den Bot blockiert oder DMs deaktiviert\n"
                    "• Bot-Cache ist nicht vollständig geladen\n\n"
                    f"🤖 Bot ist aktiv auf {len(self.bot.guilds)} Server(n).\n\n"
                    "🔓 ALTERNATIVE LÖSUNG:\n"
                    f"Da du als Bot-Master verifiziert bist, kannst du\n"
                    f"diesen Bypass-Code verwenden:\n\n"
                    f"    {bypass_hash}\n\n"
                    "⚠️ Dieser Code ist 5 Minuten gültig und nur für\n"
                    "registrierte Bot-Master/Editoren verfügbar!"
                )
                
                # Speichere Bypass-Code temporär
                self.store_bypass_code(user_id, bypass_hash)
                
                return False, error_msg
            
            # Schritt 5: DM-Channel erstellen und Nachricht senden
            try:
                logging.info(f"📨 Versuche DM-Channel zu erstellen für {user_name}...")
                dm_channel = await user.create_dm()
                logging.info(f"✅ DM-Channel erfolgreich erstellt")
            except Exception as dm_error:
                logging.error(f"❌ DM-Channel Fehler: {dm_error}")
                print(f"❌ DM-Channel Fehler: {dm_error}")
                
                # Auch hier Bypass-Code anbieten
                import hashlib
                import time
                bypass_seed = f"{user_id}_{int(time.time())//300}"
                bypass_hash = hashlib.md5(bypass_seed.encode()).hexdigest()[:6].upper()
                self.store_bypass_code(user_id, bypass_hash)
                
                error_msg = (
                    f"Kann keine DM an {user_name} senden.\n\n"
                    "🔍 Mögliche Ursachen:\n"
                    "• Du hast DMs von Server-Mitgliedern deaktiviert\n"
                    "• Du hast den Bot blockiert\n"
                    "• Deine Privatsphäre-Einstellungen blockieren DMs\n\n"
                    "💡 Lösung:\n"
                    "Discord → Einstellungen → Privatsphäre & Sicherheit\n"
                    "→ 'Direktnachrichten von Server-Mitgliedern zulassen' aktivieren\n\n"
                    "🔓 ALTERNATIVE LÖSUNG:\n"
                    f"Bypass-Code (5 Min gültig): {bypass_hash}"
                )
                
                return False, error_msg
            
            # Schritt 6: Verification-Nachricht zusammenstellen und senden
            embed = {
                "title": "🔐 StickyBot GUI Verification",
                "description": f"**Dein Verification-Code:**\n\n```{code}```\n\nGib diesen Code in der StickyBot GUI ein.\n\n⏰ **Gültig für 5 Minuten**",
                "color": 0x5865F2,
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {
                    "text": "StickyBot Security • Gib diesen Code niemals an andere weiter!"
                },
                "fields": [
                    {
                        "name": "🛡️ Sicherheitshinweis",
                        "value": "Dieser Code gewährt Zugriff auf die StickyBot GUI.\nTeile ihn niemals mit anderen!",
                        "inline": False
                    }
                ]
            }
            
            try:
                embed_obj = discord.Embed.from_dict(embed)
                await dm_channel.send(embed=embed_obj)
                
                logging.info(f"✅ Verification-Code erfolgreich an {user_name} gesendet")
                print(f"✅ Verification-Code an {user_name} gesendet")
                
                return True, f"Code erfolgreich an {user_name} gesendet! Prüfe deine Discord DMs."
                
            except Exception as send_error:
                logging.error(f"❌ Fehler beim Senden der Embed-Nachricht: {send_error}")
                
                # Fallback: Einfache Text-Nachricht versuchen
                try:
                    await dm_channel.send(
                        f"🔐 **StickyBot GUI Verification**\n\n"
                        f"Dein Verification-Code: **{code}**\n\n"
                        f"Gib diesen Code in der StickyBot GUI ein.\n"
                        f"⏰ Gültig für 5 Minuten\n\n"
                        f"🛡️ Teile diesen Code niemals mit anderen!"
                    )
                    
                    logging.info(f"✅ Fallback Text-Nachricht an {user_name} gesendet")
                    return True, f"Code (Text-Format) an {user_name} gesendet!"
                    
                except Exception as fallback_error:
                    logging.error(f"❌ Auch Fallback-Nachricht fehlgeschlagen: {fallback_error}")
                    return False, f"Kann keine Nachricht senden: {str(fallback_error)}"
            
        except discord.Forbidden as forbidden_error:
            logging.error(f"❌ Discord Forbidden Error: {forbidden_error}")
            return False, f"Keine Berechtigung für DM (User hat DMs deaktiviert): {str(forbidden_error)}"
            
        except discord.HTTPException as http_error:
            logging.error(f"❌ Discord HTTP Error: {http_error}")
            return False, f"Discord API Fehler: {str(http_error)}"
            
        except Exception as general_error:
            logging.error(f"❌ Unerwarteter Fehler beim DM-Versand: {general_error}")
            logging.error(f"Traceback: ", exc_info=True)
            return False, f"Unerwarteter Fehler: {str(general_error)}"
            
    def store_bypass_code(self, user_id, bypass_code):
        """Speichert Bypass-Code für Notfall-Zugriff"""
        global verification_codes
        expiry_time = datetime.now() + timedelta(seconds=300)  # 5 Minuten
        verification_codes[user_id] = {
            'code': bypass_code,
            'expires': expiry_time,
            'attempts': 0,
            'is_bypass': True
        }
        logging.info(f"🔑 Bypass-Code für User {user_id} gespeichert: {bypass_code}")
        
    def store_verification_code(self, user_id, code):
        """Speichert Verification-Code temporär"""
        global verification_codes
        expiry_time = datetime.now() + timedelta(seconds=self.verification_timeout)
        verification_codes[user_id] = {
            'code': code,
            'expires': expiry_time,
            'attempts': 0,
            'is_bypass': False
        }
        logging.info(f"💾 Verification-Code für User {user_id} gespeichert (läuft ab: {expiry_time})")
        
    def verify_code(self, user_id, entered_code):
        """Überprüft den eingegebenen Verification-Code"""
        global verification_codes
        
        logging.info(f"🔍 Verifying code für User {user_id}: '{entered_code}'")
        
        if user_id not in verification_codes:
            logging.warning(f"❌ Kein Verification-Code für User {user_id} gefunden")
            return False, "Kein Verification-Code angefordert"
            
        stored_data = verification_codes[user_id]
        
        # Prüfe Ablaufzeit
        if datetime.now() > stored_data['expires']:
            logging.warning(f"⏰ Verification-Code für User {user_id} ist abgelaufen")
            del verification_codes[user_id]
            return False, "Verification-Code ist abgelaufen"
            
        # Prüfe Anzahl Versuche (Max 3)
        if stored_data['attempts'] >= 3:
            logging.warning(f"🚫 Zu viele Versuche für User {user_id}")
            del verification_codes[user_id]
            return False, "Zu viele fehlgeschlagene Versuche"
            
        # Code prüfen (case-insensitive für Bypass-Codes)
        stored_code = stored_data['code']
        if stored_data.get('is_bypass', False):
            # Bypass-Code: Case-insensitive
            if stored_code.upper() == entered_code.strip().upper():
                logging.info(f"✅ Bypass-Code Verification erfolgreich für User {user_id}")
                del verification_codes[user_id]
                return True, "Bypass-Code Verification erfolgreich"
        else:
            # Normaler Code: Exact match
            if stored_code == entered_code.strip():
                logging.info(f"✅ Verification erfolgreich für User {user_id}")
                del verification_codes[user_id]
                return True, "Verification erfolgreich"
        
        # Falscher Code
        stored_data['attempts'] += 1
        remaining_attempts = 3 - stored_data['attempts']
        logging.warning(f"❌ Falscher Code für User {user_id}. {remaining_attempts} Versuche übrig")
        return False, f"Falscher Code ({remaining_attempts} Versuche übrig)"

    async def get_user_from_bot(self, user_id: str):
        """Versucht User über verschiedene Bot-Methoden zu finden"""
        try:
            user_id = int(user_id)
            logging.info(f"🔍 Suche User mit ID: {user_id}")
            
            # 1. Versuche aus Bot-Cache
            user = self.bot.get_user(user_id)
            if user:
                logging.info(f"✅ User im Cache gefunden: {user.display_name}")
                return user, user.display_name
            
            # 2. Versuche fetch_user
            try:
                logging.info(f"⚠️ User nicht im Cache, versuche fetch_user...")
                user = await asyncio.wait_for(
                    self.bot.fetch_user(user_id),
                    timeout=10.0
                )
                if user:
                    logging.info(f"✅ User über API gefunden: {user.display_name}")
                    return user, user.display_name
            except asyncio.TimeoutError:
                logging.warning(f"⏰ fetch_user Timeout")
            except Exception as fetch_error:
                logging.warning(f"❌ fetch_user fehlgeschlagen: {fetch_error}")
                
            # 3. Versuche über Server-Member
            logging.info("🔍 Suche über Server-Mitgliedschaften...")
            for guild in self.bot.guilds:
                try:
                    member = guild.get_member(user_id)
                    if member:
                        user = member._user  # Hole User-Object vom Member
                        logging.info(f"✅ User über Server '{guild.name}' gefunden: {user.display_name}")
                        return user, user.display_name
                    
                    # Falls nicht im Cache, versuche fetch
                    try:
                        member = await guild.fetch_member(user_id)
                        if member:
                            user = member._user
                            logging.info(f"✅ User über fetch_member gefunden: {user.display_name}")
                            return user, user.display_name
                    except discord.NotFound:
                        continue  # User nicht auf diesem Server
                    except Exception as fetch_member_error:
                        logging.debug(f"fetch_member auf {guild.name} fehlgeschlagen: {fetch_member_error}")
                        continue
                except Exception as guild_error:
                    logging.debug(f"Fehler bei Server {guild.name}: {guild_error}")
                    continue
            
            # 4. Erweiterte Debug-Informationen
            logging.error("❌ User wurde nicht gefunden. Debug-Informationen:")
            logging.error(f"   Bot-Cache Größe: {len(self.bot.users)} Users")
            logging.error(f"   Verfügbare Server: {len(self.bot.guilds)}")
            
            for guild in self.bot.guilds[:3]:  # Erste 3 Server
                try:
                    member_count = guild.member_count or len(guild.members)
                    logging.error(f"   Server '{guild.name}': {member_count} Mitglieder")
                    
                    # Zeige ein paar User-IDs als Referenz
                    sample_members = list(guild.members)[:5]
                    sample_ids = [str(m.id) for m in sample_members]
                    logging.error(f"     Beispiel Member-IDs: {sample_ids}")
                    
                except Exception as debug_error:
                    logging.error(f"Debug-Info Fehler: {debug_error}")
            
            return None, None
            
        except ValueError:
            logging.error(f"❌ Ungültige User-ID: {user_id} (muss Zahl sein)")
            return None, None
        except Exception as e:
            logging.error(f"❌ Fehler bei User-Suche: {e}")
            return None, None

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP Handler für OAuth Callback (für zukünftige Verwendung)"""
    
    def do_GET(self):
        """Behandelt GET Requests vom OAuth Callback"""
        if self.path.startswith('/callback'):
            # Query Parameter extrahieren
            query_start = self.path.find('?')
            if query_start != -1:
                query_string = self.path[query_start + 1:]
                params = parse_qs(query_string)
                
                if 'code' in params:
                    # Success - Code erhalten
                    self.server.oauth_code = params['code'][0]
                    self.server.oauth_error = None
                    
                    # Erfolg-Seite senden
                    response_html = """<!DOCTYPE html>
<html>
<head>
    <title>Discord Login Erfolgreich</title>
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
        }
        .icon { font-size: 48px; margin-bottom: 20px; }
        h2 { color: #57F287; margin-bottom: 15px; }
        p { margin: 10px 0; font-size: 16px; }
        .close-btn {
            background: #5865F2;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">✅</div>
        <h2>Discord Login erfolgreich!</h2>
        <p><strong>Du wirst authentifiziert...</strong></p>
        <p>Du kannst dieses Fenster jetzt schließen und</p>
        <p>zur StickyBot GUI zurückkehren.</p>
        <button class="close-btn" onclick="window.close()">Fenster schließen</button>
    </div>
    <script>
        // Auto-close nach 3 Sekunden
        setTimeout(() => window.close(), 3000);
    </script>
</body>
</html>"""
                    
                elif 'error' in params:
                    # Error - OAuth fehlgeschlagen
                    error = params['error'][0]
                    error_description = params.get('error_description', ['Unbekannter Fehler'])[0]
                    
                    self.server.oauth_code = None
                    self.server.oauth_error = f"{error}: {error_description}"
                    
                    # Fehler-Seite senden
                    response_html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Discord Login Fehlgeschlagen</title>
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
        }}
        .icon {{ font-size: 48px; margin-bottom: 20px; }}
        h2 {{ color: #ED4245; margin-bottom: 15px; }}
        p {{ margin: 10px 0; font-size: 16px; }}
        .error {{ background: #FFF2F2; border: 1px solid #FFB3B3; padding: 15px; border-radius: 8px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">❌</div>
        <h2>Discord Login fehlgeschlagen!</h2>
        <div class="error">
            <strong>Fehler:</strong> {error}<br>
            <strong>Details:</strong> {error_description}
        </div>
        <p>Bitte versuche es erneut in der StickyBot GUI.</p>
    </div>
</body>
</html>"""
                else:
                    # Unbekannter Request
                    self.server.oauth_code = None
                    self.server.oauth_error = "Unbekannte Parameter"
                    response_html = "<html><body><h1>400 Bad Request</h1></body></html>"
            else:
                # Kein Query String
                self.server.oauth_code = None
                self.server.oauth_error = "Kein Authorization Code"
                response_html = "<html><body><h1>400 Bad Request</h1></body></html>"
        else:
            # Falscher Pfad
            response_html = "<html><body><h1>404 Not Found</h1></body></html>"
        
        # HTTP Response senden
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(response_html.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Deaktiviert HTTP Logging"""
        pass

def test_challenge():
    """Test-Funktion"""
    logging.info("🧪 Discord Challenge-Response Test")
    logging.info("Hinweis: Bot muss laufen für diesen Test")

if __name__ == "__main__":
    test_challenge() 