import os
import sys
from dotenv import load_dotenv
import pathlib

# Stelle sicher, dass utils importiert werden können
try:
    from src.utils.db_manager import load_json_file
except ImportError:
    # Fallback falls Import nicht möglich (vermeidet Circular Import)
    def load_json_file(file_path, default=None):
        try:
            import json
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return default if default is not None else {}
        except:
            return default if default is not None else {}

# .env Datei laden (falls vorhanden)
load_dotenv()

def get_base_path():
    # Wenn als .exe ausgeführt
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    # Wenn als Python-Skript ausgeführt
    return pathlib.Path(__file__).parent.parent.parent

# Basisverzeichnis des Projekts
BASE_DIR = get_base_path()

# Lade Umgebungsvariablen
if isinstance(BASE_DIR, pathlib.Path):
    load_dotenv(BASE_DIR / '.env')
    DATA_DIR = BASE_DIR / 'data'
    STICKY_FILE = DATA_DIR / 'sticky_messages.json'
    BOT_ROLES_FILE = DATA_DIR / 'bot_roles.json'
else:
    load_dotenv(os.path.join(BASE_DIR, '.env'))
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    STICKY_FILE = os.path.join(DATA_DIR, 'sticky_messages.json')
    BOT_ROLES_FILE = os.path.join(DATA_DIR, 'bot_roles.json')

# Erstelle data Verzeichnis falls es nicht existiert
if isinstance(DATA_DIR, pathlib.Path):
    DATA_DIR.mkdir(exist_ok=True)
else:
    os.makedirs(DATA_DIR, exist_ok=True)

# Token aus Umgebungsvariable laden
TOKEN = os.getenv('DISCORD_TOKEN')

# Bot Konfiguration - KEIN ValueError mehr!
# Token wird zur Laufzeit durch GUI oder .env geladen

# Bot Einstellungen
DEFAULT_PREFIX = '/'

# Farben
COLORS = {
    'blue': 0x3498db,
    'green': 0x2ecc71,
    'red': 0xe74c3c,
    'yellow': 0xf1c40f,
}

def get_bot_owner_id():
    """
    Bestimmt die Bot Owner ID basierend auf der Person, die als erstes /setup_botmaster verwendet hat.
    Falls mehrere Bot Master existieren, wird der erste in der Liste als Owner betrachtet.
    """
    try:
        bot_roles = load_json_file(BOT_ROLES_FILE, {})
        if bot_roles:
            # Finde den ersten Bot Master als Owner
            for guild_id, roles in bot_roles.items():
                if 'master' in roles:
                    return int(roles['master'])
        return None
    except:
        return None

# Bot Owner ID (wird dynamisch bestimmt)
BOT_OWNER_ID = get_bot_owner_id()

# Debug-Info nur bei direkter Ausführung
if __name__ == "__main__":
    if TOKEN:
        print(f"✅ Token geladen: {TOKEN[:10]}...{TOKEN[-4:]}")
    else:
        print("ℹ️ Kein Token in .env gefunden - GUI-Setup wird verwendet")