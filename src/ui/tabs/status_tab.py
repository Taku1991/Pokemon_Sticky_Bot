"""
Status Tab für Bot-Kontrollzentrum
"""
import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime
from src.ui.tabs.base_tab import BaseTab
from src.config.constants import WINDOW_CONFIG


class StatusTab(BaseTab):
    def __init__(self, parent_frame, main_window):
        self.log_text = None
        self.status_label = None
        self.info_label = None
        self.start_btn = None
        self.stop_btn = None
        super().__init__(parent_frame, main_window)
        
    def setup_ui(self):
        """Setup des Status Tab UI"""
        # Header
        self.create_header("🤖 Sticky-Bot Kontrollzentrum", self.colors['primary'])
        
        # Status Info Frame
        info_frame = tk.Frame(self.frame, bg=self.colors['secondary'], relief='flat')
        info_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        info_inner = tk.Frame(info_frame, bg=self.colors['secondary'])
        info_inner.pack(padx=15, pady=10)
        
        # Bot Status
        self.status_label = tk.Label(info_inner,
                                    text="⏸️ Bot gestoppt",
                                    font=('Segoe UI', 14, 'bold'),
                                    fg=self.colors['error'],
                                    bg=self.colors['secondary'])
        self.status_label.pack(anchor='w')
        
        # Bot Info
        self.info_label = tk.Label(info_inner,
                                  text="Bereit zum Starten...",
                                  font=('Segoe UI', 11),
                                  fg=self.colors['text_secondary'],
                                  bg=self.colors['secondary'])
        self.info_label.pack(anchor='w', pady=(5, 0))
        
        # Control Buttons Frame
        control_frame = tk.Frame(self.frame, bg=self.colors['background'])
        control_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        # Start Button
        self.start_btn = tk.Button(control_frame,
                                  text="▶️ BOT STARTEN",
                                  command=self.start_bot,
                                  font=('Segoe UI', 14, 'bold'),
                                  bg=self.colors['success'],
                                  fg=self.colors['text_primary'],
                                  activebackground='#00a085',
                                  activeforeground=self.colors['text_primary'],
                                  relief='flat',
                                  bd=0,
                                  cursor='hand2',
                                  height=2)
        self.start_btn.pack(side='left', fill='x', expand=True, ipady=10, padx=(0, 5))
        
        # Stop Button
        self.stop_btn = tk.Button(control_frame,
                                 text="⏹️ BOT STOPPEN",
                                 command=self.stop_bot,
                                 font=('Segoe UI', 14, 'bold'),
                                 bg=self.colors['error'],
                                 fg=self.colors['text_primary'],
                                 activebackground='#c73e41',
                                 activeforeground=self.colors['text_primary'],
                                 relief='flat',
                                 bd=0,
                                 cursor='hand2',
                                 height=2,
                                 state='disabled')
        self.stop_btn.pack(side='right', fill='x', expand=True, ipady=10, padx=(5, 0))
        
        # Log Bereich
        log_frame = tk.Frame(self.frame, bg=self.colors['background'])
        log_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        log_label = tk.Label(log_frame,
                            text="📋 Bot-Log:",
                            font=('Segoe UI', 12, 'bold'),
                            fg=self.colors['text_primary'],
                            bg=self.colors['background'])
        log_label.pack(anchor='w', pady=(0, 5))
        
        # Scrollbares Text-Widget für Logs
        self.log_text = scrolledtext.ScrolledText(log_frame,
                                                 font=('Consolas', 9),
                                                 bg='#40444B',
                                                 fg='#DCDDDE',
                                                 insertbackground='#FFFFFF',
                                                 relief='flat',
                                                 wrap=tk.WORD,
                                                 height=12)
        self.log_text.pack(fill='both', expand=True)
        
        # Button Frame für zusätzliche Funktionen
        button_frame = tk.Frame(self.frame, bg=self.colors['background'])
        button_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        # Restart Button
        restart_btn = self.create_button(button_frame, "🔄 Neu starten", 
                                        self.restart_bot, self.colors['warning'])
        restart_btn.pack(side='left', ipady=8, ipadx=15)
        
        # Token Setup Button
        token_btn = self.create_button(button_frame, "🔑 Token ändern", 
                                      self.change_token, self.colors['primary'])
        token_btn.pack(side='left', padx=(10, 0), ipady=8, ipadx=15)
        
        # Beenden Button
        quit_btn = self.create_button(button_frame, "❌ Programm beenden", 
                                     self.main_window.on_closing, '#4F545C')
        quit_btn.pack(side='right', ipady=8, ipadx=15)
    
    def start_bot(self):
        """Startet den Bot"""
        if hasattr(self.main_window, 'bot_manager') and self.main_window.bot_manager:
            self.add_log("▶️ Bot wird gestartet...")
            self.update_status("🔄 Bot startet...", "Verbindung wird aufgebaut...", self.colors['warning'])
            
            # Buttons aktualisieren
            self.start_btn.config(state='disabled')
            self.stop_btn.config(state='normal')
            
            # Bot in separatem Thread starten
            self.main_window.bot_manager.start_bot_thread()
        else:
            self.add_log("❌ Bot Manager nicht verfügbar!")
    
    def stop_bot(self):
        """Stoppt den Bot"""
        if hasattr(self.main_window, 'bot_manager') and self.main_window.bot_manager:
            self.main_window.bot_manager.stop_bot()
        else:
            self.add_log("❌ Bot Manager nicht verfügbar!")
    
    def restart_bot(self):
        """Startet den Bot neu"""
        if hasattr(self.main_window, 'bot_manager') and self.main_window.bot_manager:
            self.main_window.bot_manager.restart_bot()
        else:
            self.add_log("❌ Bot Manager nicht verfügbar!")
            
    def change_token(self):
        """Öffnet das Token-Setup"""
        if hasattr(self.main_window, 'bot_manager') and self.main_window.bot_manager:
            self.main_window.bot_manager.change_token()
        else:
            self.add_log("❌ Bot Manager nicht verfügbar!")
    
    def add_log(self, message):
        """Fügt eine Log-Nachricht hinzu"""
        if not self.log_text:
            return
            
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        # Im GUI-Thread ausführen
        self.main_window.root.after(0, self._add_log_safe, formatted_message)
        
    def _add_log_safe(self, message):
        """Thread-sichere Log-Hinzufügung"""
        try:
            if self.log_text:
                self.log_text.insert(tk.END, message)
                self.log_text.see(tk.END)  # Automatisch nach unten scrollen
                
                # Begrenze die Anzahl der Zeilen (letzte 1000 behalten)
                lines = self.log_text.get("1.0", tk.END).split('\n')
                if len(lines) > 1000:
                    self.log_text.delete("1.0", f"{len(lines)-1000}.0")
        except:
            pass  # Ignoriere Fehler wenn Fenster geschlossen wird
            
    def update_status(self, status, info="", color=None):
        """Aktualisiert den Bot-Status"""
        if not color:
            color = self.colors['warning']
        self.main_window.root.after(0, self._update_status_safe, status, info, color)
        
    def _update_status_safe(self, status, info, color):
        """Thread-sichere Status-Aktualisierung"""
        try:
            if self.status_label:
                self.status_label.config(text=status, fg=color)
            if self.info_label:
                self.info_label.config(text=info)
        except:
            pass 