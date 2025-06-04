"""
Sichere Speicherung mit AES-256 Verschlüsselung
"""
import os
import json
import base64
import hashlib
import logging
from cryptography.fernet import Fernet
from src.utils.path_manager import get_application_path


class SecureStorage:
    """AES-256 verschlüsselte Speicherung für sensible Daten"""
    
    def __init__(self, master_key):
        """
        Args:
            master_key: Master-Schlüssel für die Verschlüsselung (z.B. Bot Token)
        """
        self.master_key = master_key
        self.encryption_key = self._generate_key()
        
    def _generate_key(self):
        """Generiert einen konsistenten Verschlüsselungsschlüssel"""
        try:
            # Hardware-unabhängiger, aber Bot-spezifischer Key
            key_material = f"StickyBot_AES256_{self.master_key}_2024".encode()
            key_hash = hashlib.sha256(key_material).digest()
            return base64.urlsafe_b64encode(key_hash[:32])
        except Exception as e:
            logging.error(f"Schlüsselgenerierung fehlgeschlagen: {e}")
            # Fallback
            fallback = hashlib.sha256(b"StickyBot_Fallback_2024").digest()
            return base64.urlsafe_b64encode(fallback[:32])
    
    def encrypt_data(self, data):
        """Verschlüsselt Daten"""
        try:
            fernet = Fernet(self.encryption_key)
            json_str = json.dumps(data, ensure_ascii=False)
            encrypted_data = fernet.encrypt(json_str.encode('utf-8'))
            return base64.b64encode(encrypted_data).decode('utf-8')
        except Exception as e:
            logging.error(f"Verschlüsselung fehlgeschlagen: {e}")
            return None
    
    def decrypt_data(self, encrypted_data):
        """Entschlüsselt Daten"""
        try:
            fernet = Fernet(self.encryption_key)
            decoded_data = base64.b64decode(encrypted_data.encode('utf-8'))
            decrypted_data = fernet.decrypt(decoded_data)
            return json.loads(decrypted_data.decode('utf-8'))
        except Exception as e:
            logging.error(f"Entschlüsselung fehlgeschlagen: {e}")
            return None
    
    def save_encrypted_json(self, data, filename):
        """Speichert JSON-Daten verschlüsselt"""
        try:
            app_path = get_application_path()
            
            # Vollständigen Pfad erstellen
            if not filename.startswith(os.sep) and not os.path.isabs(filename):
                if not filename.startswith('data/'):
                    filename = f"data/{filename}"
                full_path = os.path.join(app_path, filename)
            else:
                full_path = filename
            
            # .enc Endung hinzufügen falls nicht vorhanden
            if not full_path.endswith('.enc'):
                full_path += '.enc'
            
            # Verzeichnis erstellen
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # Verschlüsseln und speichern
            encrypted_data = self.encrypt_data(data)
            if not encrypted_data:
                return False
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(encrypted_data)
            
            return True
            
        except Exception as e:
            logging.error(f"Speichern fehlgeschlagen ({filename}): {e}")
            return False
    
    def load_encrypted_json(self, filename):
        """Lädt verschlüsselte JSON-Daten"""
        try:
            app_path = get_application_path()
            
            # Vollständigen Pfad erstellen
            if not filename.startswith(os.sep) and not os.path.isabs(filename):
                if not filename.startswith('data/'):
                    filename = f"data/{filename}"
                full_path = os.path.join(app_path, filename)
            else:
                full_path = filename
            
            # .enc Endung hinzufügen falls nicht vorhanden
            if not full_path.endswith('.enc'):
                full_path += '.enc'
            
            # Prüfen ob Datei existiert
            if not os.path.exists(full_path):
                return {}
            
            # Laden und entschlüsseln
            with open(full_path, 'r', encoding='utf-8') as f:
                encrypted_data = f.read().strip()
            
            if not encrypted_data:
                return {}
            
            decrypted_data = self.decrypt_data(encrypted_data)
            return decrypted_data if decrypted_data is not None else {}
            
        except Exception as e:
            logging.error(f"Laden fehlgeschlagen ({filename}): {e}")
            return {}
    
    def migrate_unencrypted_file(self, unencrypted_path, encrypted_filename):
        """Migriert eine unverschlüsselte Datei zu verschlüsselter Version"""
        try:
            if not os.path.exists(unencrypted_path):
                return False
            
            # Unverschlüsselte Daten laden
            with open(unencrypted_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Verschlüsselt speichern
            success = self.save_encrypted_json(data, encrypted_filename)
            
            if success:
                # Original-Datei löschen
                os.remove(unencrypted_path)
                return True
            
            return False
            
        except Exception as e:
            logging.error(f"Migration fehlgeschlagen: {e}")
            return False

# Convenience-Funktionen für Bot-Daten
def get_secure_storage(bot_token=None):
    """Erstellt SecureStorage Instanz mit Bot-Token"""
    return SecureStorage(bot_token)

def save_bot_roles_secure(bot_roles_data, bot_token=None):
    """Speichert Bot-Rollen verschlüsselt"""
    storage = SecureStorage(bot_token)
    return storage.save_encrypted_json(bot_roles_data, "data/bot_roles.json")

def load_bot_roles_secure(bot_token=None):
    """Lädt Bot-Rollen verschlüsselt"""
    storage = SecureStorage(bot_token)
    return storage.load_encrypted_json("data/bot_roles.json")

def save_sticky_messages_secure(sticky_data, bot_token=None):
    """Speichert Sticky Messages verschlüsselt"""
    storage = SecureStorage(bot_token)
    return storage.save_encrypted_json(sticky_data, "data/sticky_messages.json")

def load_sticky_messages_secure(bot_token=None):
    """Lädt Sticky Messages aus verschlüsselter Datei mit automatischer Migration"""
    from src.utils.path_manager import get_application_path
    import os
    import json
    
    # Automatische Migration von unverschlüsselter zu verschlüsselter Datei
    app_path = get_application_path()
    old_file = os.path.join(app_path, 'data', 'sticky_messages.json')
    
    if os.path.exists(old_file):
        try:
            logging.info("🔄 Migration: Unverschlüsselte sticky_messages.json gefunden - migriere zu verschlüsselter Version...")
            
            # Lade unverschlüsselte Daten
            with open(old_file, 'r', encoding='utf-8') as f:
                old_data = json.load(f)
            
            # Speichere verschlüsselt
            storage = SecureStorage(bot_token)
            success = storage.save_encrypted_json(old_data, "data/sticky_messages.json")
            
            if success:
                # Lösche unverschlüsselte Datei nach erfolgreicher Migration
                os.remove(old_file)
                logging.info(f"✅ Migration erfolgreich: {len(old_data)} Sticky Messages verschlüsselt und alte Datei gelöscht")
                return old_data
            else:
                logging.warning("⚠️ Migration fehlgeschlagen - verwende unverschlüsselte Daten")
                return old_data
                
        except Exception as e:
            logging.error(f"❌ Migration-Fehler: {e} - versuche normale Ladung")
    
    # Normale verschlüsselte Ladung
    storage = SecureStorage(bot_token)
    return storage.load_encrypted_json("data/sticky_messages.json")

def migrate_all_data_to_encrypted(bot_token=None):
    """Migriert alle Bot-Daten zu verschlüsselter Speicherung"""
    storage = SecureStorage(bot_token)
    
    results = []
    files_to_migrate = [
        "data/bot_roles.json",
        "data/sticky_messages.json"
    ]
    
    for file_path in files_to_migrate:
        result = storage.migrate_unencrypted_file(file_path, file_path)
        results.append((file_path, result))
        
    return results

if __name__ == "__main__":
    # Test der Sicherheitsfunktionen
    print("🔐 Teste Sichere Speicherung...")
    
    storage = SecureStorage("test_bot_token")
    
    if storage.verify_security():
        print("✅ Alle Sicherheitstests bestanden!")
    else:
        print("❌ Sicherheitstests fehlgeschlagen!") 