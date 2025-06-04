class BotError(Exception):
    """Basis-Ausnahmeklasse für Bot-spezifische Fehler"""
    pass

class PermissionError(BotError):
    """Wird ausgelöst, wenn ein Benutzer keine Berechtigung für eine Aktion hat"""
    pass

class ConfigError(BotError):
    """Wird ausgelöst, wenn es Probleme mit der Konfiguration gibt"""
    pass