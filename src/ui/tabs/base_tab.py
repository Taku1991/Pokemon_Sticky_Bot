"""
Basis-Klasse für alle Tab-Module
"""
import tkinter as tk
from src.config.constants import WINDOW_CONFIG


class BaseTab:
    def __init__(self, parent_frame, main_window):
        self.parent_frame = parent_frame
        self.main_window = main_window
        self.colors = WINDOW_CONFIG['colors']
        
        # Tab Frame erstellen
        self.frame = tk.Frame(parent_frame, bg=self.colors['background'])
        
        # Setup UI
        self.setup_ui()
        
    def setup_ui(self):
        """Override in Subclasses"""
        pass
        
    def show(self):
        """Zeigt den Tab an"""
        self.frame.pack(fill='both', expand=True)
        
    def hide(self):
        """Versteckt den Tab"""
        self.frame.pack_forget()
        
    def create_header(self, title, bg_color):
        """Erstellt einen Header für den Tab"""
        header_frame = tk.Frame(self.frame, bg=bg_color, relief='flat')
        header_frame.pack(fill='x', pady=(0, 15), padx=10)
        
        title_label = tk.Label(header_frame, 
                              text=title, 
                              font=('Segoe UI', 16, 'bold'),
                              fg=self.colors['text_primary'], 
                              bg=bg_color)
        title_label.pack(pady=12)
        
        return header_frame
        
    def create_button(self, parent, text, command, bg_color, **kwargs):
        """Erstellt einen Button mit verbessertem Styling und Hover-Effekten"""
        
        # Bestimme Hover-Farbe basierend auf Hauptfarbe
        hover_color = bg_color
        if bg_color == self.colors['primary']:
            hover_color = self.colors['primary_hover']
        elif bg_color == self.colors['success']:
            hover_color = self.colors['success_hover']
        elif bg_color == self.colors['warning']:
            hover_color = self.colors['warning_hover']
        elif bg_color == self.colors['error']:
            hover_color = self.colors['error_hover']
        elif bg_color == self.colors['secondary']:
            hover_color = self.colors['secondary_hover']
        else:
            # Fallback: Farbe etwas dunkler machen
            hover_color = self._darken_color(bg_color)
        
        default_kwargs = {
            'font': ('Segoe UI', 11, 'bold'),
            'fg': self.colors['button_text'],
            'activebackground': hover_color,
            'activeforeground': self.colors['button_text'],
            'relief': 'raised',
            'bd': 2,
            'cursor': 'hand2',
            'padx': 10,
            'pady': 5
        }
        default_kwargs.update(kwargs)
        
        button = tk.Button(parent, text=text, command=command, bg=bg_color, **default_kwargs)
        
        # Hover-Effekte hinzufügen
        def on_enter(event):
            button.config(bg=hover_color, relief='raised')
        
        def on_leave(event):
            button.config(bg=bg_color, relief='raised')
            
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
        
        return button
    
    def _darken_color(self, hex_color):
        """Verdunkelt eine Hex-Farbe um 20%"""
        try:
            # Entferne '#' falls vorhanden
            hex_color = hex_color.lstrip('#')
            
            # Konvertiere zu RGB
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            
            # Verdunkle um 20%
            r = max(0, int(r * 0.8))
            g = max(0, int(g * 0.8))
            b = max(0, int(b * 0.8))
            
            # Zurück zu Hex
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            # Fallback
            return '#40444B' 