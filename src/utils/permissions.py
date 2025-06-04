"""
Berechtigungsverwaltung für Sticky-Bot
Behandelt Bot Master und Bot Editor Berechtigungen pro Server
Kompatibel mit bestehender bot_roles.json Struktur
🔐 Jetzt mit AES-256 Verschlüsselung!
"""
import os
import json
import logging
from src.utils.path_manager import get_application_path
from src.utils.secure_storage import SecureStorage


def get_bot_token():
    """Holt den Bot Token für die Verschlüsselung"""
    try:
        # 1. HÖCHSTE PRIORITÄT: Direkt aus .env Datei laden
        app_path = get_application_path()
        env_file = os.path.join(app_path, '.env')
        
        if os.path.exists(env_file):
            try:
                with open(env_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    for line in content.splitlines():
                        if line.strip().startswith('DISCORD_TOKEN='):
                            token = line.split('=', 1)[1].strip()
                            token = token.strip('"').strip("'")
                            if token and len(token) > 20:
                                return token
            except Exception as e:
                logging.warning(f"Fehler beim .env Lesen: {e}")
        
        # 2. Fallback: Umgebungsvariablen
        import os as env_os
        env_token = env_os.getenv('DISCORD_TOKEN')
        if env_token:
            env_token = env_token.strip('"').strip("'")
            if env_token and len(env_token) > 20:
                return env_token
        
        # 3. Aus Bot-Instanzen
        import sys
        main_module = sys.modules.get('__main__')
        if main_module:
            if hasattr(main_module, 'bot') and main_module.bot:
                bot = main_module.bot
                if hasattr(bot, 'token') and bot.token:
                    bot_token = str(bot.token).strip('"').strip("'")
                    if bot_token and len(bot_token) > 20:
                        return bot_token
                        
                if hasattr(bot, 'http') and hasattr(bot.http, 'token') and bot.http.token:
                    http_token = str(bot.http.token).strip('"').strip("'")
                    if http_token and len(http_token) > 20:
                        return http_token
            
            if hasattr(main_module, 'bot_manager') and main_module.bot_manager:
                bot_manager = main_module.bot_manager
                if hasattr(bot_manager, 'bot') and bot_manager.bot:
                    bot = bot_manager.bot
                    if hasattr(bot, 'token') and bot.token:
                        manager_token = str(bot.token).strip('"').strip("'")
                        if manager_token and len(manager_token) > 20:
                            return manager_token
                            
                    if hasattr(bot, 'http') and hasattr(bot.http, 'token') and bot.http.token:
                        manager_http_token = str(bot.http.token).strip('"').strip("'")
                        if manager_http_token and len(manager_http_token) > 20:
                            return manager_http_token
        
        # 4. Hardware-spezifischer Fallback
        import platform
        import uuid
        import hashlib
        
        machine_id = platform.machine()
        node_id = str(uuid.getnode())
        system = platform.system()
        
        fallback_data = f"StickyBot_Fallback_{machine_id}_{node_id}_{system}_2024"
        fallback_key = hashlib.sha256(fallback_data.encode()).hexdigest()[:64]
        
        logging.warning("Bot Token nicht gefunden - verwende Hardware-Fallback")
        return fallback_key
        
    except Exception as e:
        logging.error(f"Kritischer Fehler beim Token-Abruf: {e}")
        return "critical_fallback_sticky_bot_emergency_key_2024"


def get_permissions_file():
    """Gibt den Pfad zur Berechtigungsdatei zurück"""
    app_path = get_application_path()
    data_dir = os.path.join(app_path, 'data')
    
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    return os.path.join(data_dir, 'bot_roles.json')


def load_permissions():
    """Lädt die Berechtigungen aus der verschlüsselten bot_roles.json"""
    try:
        bot_token = get_bot_token()
        storage = SecureStorage(bot_token)
        
        bot_roles = storage.load_encrypted_json("data/bot_roles.json")
        
        if not bot_roles:
            # Migration von unverschlüsselter Datei
            app_path = get_application_path()
            bot_roles_file = os.path.join(app_path, 'data', 'bot_roles.json')
            
            if os.path.exists(bot_roles_file):
                with open(bot_roles_file, 'r', encoding='utf-8') as f:
                    bot_roles = json.load(f)
                
                save_permissions_from_bot_roles(bot_roles)
                os.remove(bot_roles_file)
            else:
                bot_roles = {}
        
        # Konvertiere zu internem Format
        permissions = {}
        for guild_id, roles in bot_roles.items():
            permissions[guild_id] = {
                'masters': roles.get('admin', []),
                'editors': roles.get('editor', [])
            }
        
        return permissions
        
    except Exception as e:
        logging.error(f"Fehler beim Laden der Berechtigungen: {e}")
        return {}


def save_permissions(permissions):
    """Speichert die Berechtigungen verschlüsselt"""
    try:
        bot_roles = {}
        for guild_id, perms in permissions.items():
            bot_roles[guild_id] = {
                'admin': perms.get('masters', []),
                'editor': perms.get('editors', []),
                'viewer': []
            }
        
        return save_permissions_from_bot_roles(bot_roles)
        
    except Exception as e:
        logging.error(f"Fehler beim Speichern der Berechtigungen: {e}")
        return False


def save_permissions_from_bot_roles(bot_roles):
    """Speichert bot_roles Format verschlüsselt"""
    try:
        bot_token = get_bot_token()
        storage = SecureStorage(bot_token)
        
        success = storage.save_encrypted_json(bot_roles, "data/bot_roles.json")
        
        if success:
            return True
        else:
            raise Exception("Verschlüsseltes Speichern fehlgeschlagen")
            
    except Exception as e:
        logging.error(f"Fehler beim verschlüsselten Speichern: {e}")
        
        # Fallback auf unverschlüsselte Speicherung
        try:
            app_path = get_application_path()
            data_dir = os.path.join(app_path, 'data')
            bot_roles_file = os.path.join(data_dir, 'bot_roles.json')
            
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
            
            with open(bot_roles_file, 'w', encoding='utf-8') as f:
                json.dump(bot_roles, f, indent=2, ensure_ascii=False)
                
            logging.warning("Berechtigungen unverschlüsselt gespeichert (Fallback)")
            return True
            
        except Exception as fallback_error:
            logging.error(f"Auch Fallback-Speichern fehlgeschlagen: {fallback_error}")
            return False


def is_bot_admin(user_id, guild_id):
    """Prüft ob ein User Bot Master ist"""
    try:
        permissions = load_permissions()
        guild_str = str(guild_id)
        user_str = str(user_id)
        
        if guild_str not in permissions:
            return False
        
        masters = permissions[guild_str].get('masters', [])
        return user_str in masters
        
    except Exception as e:
        logging.error(f"Fehler bei Bot Admin Prüfung: {e}")
        return False


def is_bot_editor(user_id, guild_id):
    """Prüft ob ein User Bot Editor ist"""
    try:
        permissions = load_permissions()
        guild_str = str(guild_id)
        user_str = str(user_id)
        
        if guild_str not in permissions:
            return False
        
        editors = permissions[guild_str].get('editors', [])
        return user_str in editors
        
    except Exception as e:
        logging.error(f"Fehler bei Bot Editor Prüfung: {e}")
        return False


def has_bot_permissions(user_id, guild_id):
    """Prüft ob ein User Bot Master ODER Bot Editor ist"""
    return is_bot_admin(user_id, guild_id) or is_bot_editor(user_id, guild_id)


def add_bot_master(user_id, guild_id):
    """Fügt einen Bot Master hinzu"""
    try:
        permissions = load_permissions()
        guild_str = str(guild_id)
        user_str = str(user_id)
        
        if guild_str not in permissions:
            permissions[guild_str] = {'masters': [], 'editors': []}
        
        # User von Editors entfernen falls vorhanden
        if user_str in permissions[guild_str].get('editors', []):
            permissions[guild_str]['editors'].remove(user_str)
        
        # Als Master hinzufügen falls noch nicht vorhanden
        if user_str not in permissions[guild_str].get('masters', []):
            permissions[guild_str]['masters'].append(user_str)
        
        return save_permissions(permissions)
        
    except Exception as e:
        logging.error(f"Fehler beim Hinzufügen des Bot Masters: {e}")
        return False


def add_bot_editor(user_id, guild_id):
    """Fügt einen Bot Editor hinzu"""
    try:
        permissions = load_permissions()
        guild_str = str(guild_id)
        user_str = str(user_id)
        
        if guild_str not in permissions:
            permissions[guild_str] = {'masters': [], 'editors': []}
        
        # Prüfen ob bereits Master
        if user_str in permissions[guild_str].get('masters', []):
            return True
        
        # Als Editor hinzufügen falls noch nicht vorhanden
        if user_str not in permissions[guild_str].get('editors', []):
            permissions[guild_str]['editors'].append(user_str)
        
        return save_permissions(permissions)
        
    except Exception as e:
        logging.error(f"Fehler beim Hinzufügen des Bot Editors: {e}")
        return False


def remove_bot_permissions(user_id, guild_id):
    """Entfernt alle Bot-Berechtigungen eines Users"""
    try:
        permissions = load_permissions()
        guild_str = str(guild_id)
        user_str = str(user_id)
        
        if guild_str not in permissions:
            return True
        
        removed = False
        
        if user_str in permissions[guild_str].get('masters', []):
            permissions[guild_str]['masters'].remove(user_str)
            removed = True
        
        if user_str in permissions[guild_str].get('editors', []):
            permissions[guild_str]['editors'].remove(user_str)
            removed = True
        
        if removed:
            return save_permissions(permissions)
        else:
            return True
        
    except Exception as e:
        logging.error(f"Fehler beim Entfernen der Bot-Berechtigungen: {e}")
        return False


def get_server_permissions(guild_id):
    """Gibt alle Berechtigungen für einen Server zurück"""
    try:
        permissions = load_permissions()
        guild_str = str(guild_id)
        
        return permissions.get(guild_str, {'masters': [], 'editors': []})
        
    except Exception as e:
        logging.error(f"Fehler beim Abrufen der Server-Berechtigungen: {e}")
        return {'masters': [], 'editors': []}


def get_user_permissions(user_id):
    """Gibt alle Server zurück auf denen ein User Berechtigungen hat"""
    try:
        permissions = load_permissions()
        user_str = str(user_id)
        user_permissions = {}
        
        for guild_str, guild_perms in permissions.items():
            if user_str in guild_perms.get('masters', []):
                user_permissions[guild_str] = 'master'
            elif user_str in guild_perms.get('editors', []):
                user_permissions[guild_str] = 'editor'
        
        return user_permissions
        
    except Exception as e:
        logging.error(f"Fehler beim Abrufen der User-Berechtigungen: {e}")
        return {}


def cleanup_permissions():
    """Bereinigt leere Guild-Einträge"""
    try:
        permissions = load_permissions()
        cleaned_permissions = {}
        
        for guild_str, guild_perms in permissions.items():
            masters = guild_perms.get('masters', [])
            editors = guild_perms.get('editors', [])
            
            if masters or editors:
                cleaned_permissions[guild_str] = guild_perms
        
        if len(cleaned_permissions) != len(permissions):
            return save_permissions(cleaned_permissions)
        
        return True
        
    except Exception as e:
        logging.error(f"Fehler bei der Bereinigung der Berechtigungen: {e}")
        return False


def export_permissions_text():
    """Exportiert die Berechtigungen als Text"""
    try:
        permissions = load_permissions()
        
        if not permissions:
            return "Keine Berechtigungen konfiguriert."
        
        lines = ["=== STICKY-BOT BERECHTIGUNGEN ===", ""]
        
        for guild_str, guild_perms in permissions.items():
            lines.append(f"🏠 Server: {guild_str}")
            
            masters = guild_perms.get('masters', [])
            if masters:
                lines.append(f"  👑 Bot Masters ({len(masters)}):")
                for user_id in masters:
                    lines.append(f"    - {user_id}")
            else:
                lines.append("  👑 Bot Masters: Keine")
            
            editors = guild_perms.get('editors', [])
            if editors:
                lines.append(f"  ✏️ Bot Editors ({len(editors)}):")
                for user_id in editors:
                    lines.append(f"    - {user_id}")
            else:
                lines.append("  ✏️ Bot Editors: Keine")
            
            lines.append("")
        
        return "\n".join(lines)
        
    except Exception as e:
        logging.error(f"Fehler beim Export der Berechtigungen: {e}")
        return f"Fehler beim Export: {str(e)}"


def initialize_permissions():
    """Initialisiert das Berechtigungssystem"""
    try:
        app_path = get_application_path()
        permissions_file = os.path.join(app_path, 'data', 'bot_roles.json')
        encrypted_permissions_file = os.path.join(app_path, 'data', 'bot_roles.json.enc')
        
        # Prüfe auf verschlüsselte Datei
        if os.path.exists(encrypted_permissions_file):
            perms = load_permissions()
            return
        
        # Prüfe auf unverschlüsselte Legacy-Datei
        if os.path.exists(permissions_file):
            with open(permissions_file, 'r', encoding='utf-8') as f:
                bot_roles = json.load(f)
            
            success = save_permissions_from_bot_roles(bot_roles)
            if success:
                os.remove(permissions_file)
            return
            
        # Erstelle neue leere Struktur
        data_dir = os.path.join(app_path, 'data')
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        save_permissions({})
            
    except Exception as e:
        logging.error(f"Fehler bei der Initialisierung: {e}")


# Beim Import ausführen
initialize_permissions()


def initialize_permissions_at_startup(bot=None):
    """Initialisiert das Berechtigungssystem beim Bot-Start"""
    try:
        if bot:
            import sys
            main_module = sys.modules.get('__main__')
            if main_module and not hasattr(main_module, 'bot'):
                main_module.bot = bot
        
        permissions = load_permissions()
        
        if permissions:
            server_count = len(permissions)
            total_users = sum(len(p.get('masters', [])) + len(p.get('editors', [])) for p in permissions.values())
            logging.info(f"Berechtigungssystem initialisiert: {server_count} Server, {total_users} Benutzer")
        
        return True
        
    except Exception as e:
        logging.error(f"Fehler bei Berechtigungsinitialisierung: {e}")
        return False


def debug_permissions():
    """Debug-Funktion: Zeigt alle geladenen Berechtigungen an"""
    try:
        permissions = load_permissions()
        
        if not permissions:
            logging.info("Keine Berechtigungen gefunden")
            return
        
        logging.info(f"Gefundene Server: {len(permissions)}")
        
        for guild_id, perms in permissions.items():
            masters = perms.get('masters', [])
            editors = perms.get('editors', [])
            
            logging.info(f"Server {guild_id}: {len(masters)} Masters, {len(editors)} Editors")
        
    except Exception as e:
        logging.error(f"Debug-Fehler: {e}")


def test_permission_user(user_id, guild_id):
    """Testet die Berechtigung für einen User"""
    try:
        is_admin = is_bot_admin(user_id, guild_id)
        is_editor = is_bot_editor(user_id, guild_id)
        
        return is_admin, is_editor
        
    except Exception as e:
        logging.error(f"Test-Fehler: {e}")
        return False, False