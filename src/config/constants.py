"""
Konstanten und Konfiguration für Sticky-Bot
"""

# Liste der Cogs die geladen werden sollen
INITIAL_EXTENSIONS = [
    'src.cogs.admin',
    'src.cogs.sticky',
    'src.cogs.events',
    'src.cogs.help'
]

# GUI Konfiguration
WINDOW_CONFIG = {
    'title': '🤖 Sticky-Bot - Kontrollzentrum',
    'geometry': '800x700',
    'colors': {
        'background': '#2C2F33',
        'primary': '#5865F2',
        'primary_hover': '#4752C4',
        'secondary': '#36393F',
        'secondary_hover': '#40444B',
        'success': '#00b894',
        'success_hover': '#00a085',
        'warning': '#FAA61A',
        'warning_hover': '#E89C0D',
        'error': '#ed4245',
        'error_hover': '#c73e41',
        'text_primary': '#FFFFFF',
        'text_secondary': '#B9BBBE',
        'text_disabled': '#72767D',
        'button_text': '#FFFFFF',
        'button_border': '#40444B',
        'input_bg': '#40444B',
        'input_fg': '#DCDDDE'
    }
}

# Tab Konfiguration
TAB_CONFIG = {
    'status': {
        'title': '📊 Bot Status',
        'color': '#5865F2',
        'hover': '#4752C4'
    },
    'sticky': {
        'title': '📝 Sticky Manager',
        'color': '#00b894',
        'hover': '#00a085'
    },
    'server': {
        'title': '🏠 Server Verwaltung',
        'color': '#FAA61A',
        'hover': '#E89C0D'
    }
}

# Logging Konfiguration
LOG_CONFIG = {
    'level': 'DEBUG',
    'format': '[%(asctime)s] [%(levelname)s] %(message)s',
    'date_format': '%Y-%m-%d %H:%M:%S',
    'max_lines': 1000
} 