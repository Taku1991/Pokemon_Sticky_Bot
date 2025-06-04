"""
Sticky Messages Tab - Vollständige Implementierung
"""
import tkinter as tk
from tkinter import messagebox, ttk
import os
import json
import logging
from datetime import datetime

from src.ui.tabs.base_tab import BaseTab
from src.ui.sticky_dialog import StickyManagerDialog
from src.utils.path_manager import get_application_path
from src.utils.permissions import is_bot_editor, is_bot_admin
from src.utils.secure_storage import load_sticky_messages_secure, save_sticky_messages_secure


class StickyTab(BaseTab):
    def __init__(self, parent_frame, main_window):
        self.sticky_listbox = None
        self.details_frame = None
        self.details_widgets = {}
        self.current_selection = None
        super().__init__(parent_frame, main_window)
        
    def setup_ui(self):
        """Setup des Sticky Tab UI"""
        # Header
        self.create_header("📝 Sticky Messages Verwaltung", self.colors['success'])
        
        # Main Container mit zwei Panels
        main_container = tk.Frame(self.frame, bg=self.colors['background'])
        main_container.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Linkes Panel - Liste der Sticky Messages
        self.setup_left_panel(main_container)
        
        # Rechtes Panel - Details und Aktionen
        self.setup_right_panel(main_container)
        
        # Button Frame für globale Aktionen
        self.setup_action_buttons()
        
        # Initial laden
        self.refresh_sticky_list()
        
    def setup_left_panel(self, parent):
        """Setup des linken Panels mit der Sticky Messages Liste"""
        left_frame = tk.Frame(parent, bg=self.colors['secondary'], relief='flat')
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        # Header für Liste
        list_header = tk.Label(left_frame,
                              text="📋 Aktive Sticky Messages",
                              font=('Segoe UI', 12, 'bold'),
                              fg=self.colors['text_primary'],
                              bg=self.colors['secondary'])
        list_header.pack(pady=(10, 5))
        
        # Listbox mit Scrollbar
        list_container = tk.Frame(left_frame, bg=self.colors['secondary'])
        list_container.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Scrollbar
        scrollbar = tk.Scrollbar(list_container)
        scrollbar.pack(side='right', fill='y')
        
        # Listbox
        self.sticky_listbox = tk.Listbox(list_container,
                                        font=('Segoe UI', 10),
                                        bg='#40444B',
                                        fg='#DCDDDE',
                                        selectbackground=self.colors['primary'],
                                        selectforeground='white',
                                        relief='flat',
                                        borderwidth=0,
                                        highlightthickness=0,
                                        yscrollcommand=scrollbar.set)
        self.sticky_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.sticky_listbox.yview)
        
        # Event Handler für Auswahl
        self.sticky_listbox.bind('<<ListboxSelect>>', self.on_sticky_select)
        
        # Doppelklick zum Bearbeiten
        self.sticky_listbox.bind('<Double-1>', self.edit_sticky)
    
    def setup_right_panel(self, parent):
        """Setup des rechten Panels mit Details"""
        self.details_frame = tk.Frame(parent, bg=self.colors['secondary'], relief='flat')
        self.details_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))
        
        # Header für Details
        details_header = tk.Label(self.details_frame,
                                 text="📄 Message Details",
                                 font=('Segoe UI', 12, 'bold'),
                                 fg=self.colors['text_primary'],
                                 bg=self.colors['secondary'])
        details_header.pack(pady=(10, 15))
        
        # Placeholder für Details
        self.show_empty_details()
    
    def setup_action_buttons(self):
        """Setup der Aktions-Buttons"""
        button_frame = tk.Frame(self.frame, bg=self.colors['background'])
        button_frame.pack(fill='x', padx=10, pady=(10, 0))
        
        # Neue Sticky Message erstellen
        create_btn = self.create_button(button_frame, "➕ Neue Sticky Message", 
                                       self.create_new_sticky, self.colors['success'])
        create_btn.pack(side='left', ipady=8, ipadx=15)
        
        # Bearbeiten Button
        self.edit_btn = self.create_button(button_frame, "✏️ Bearbeiten", 
                                          self.edit_sticky, self.colors['primary'])
        self.edit_btn.pack(side='left', padx=(10, 0), ipady=8, ipadx=15)
        self.edit_btn.config(state='disabled')
        
        # Löschen Button
        self.delete_btn = self.create_button(button_frame, "🗑️ Löschen", 
                                            self.delete_sticky, self.colors['error'])
        self.delete_btn.pack(side='left', padx=(10, 0), ipady=8, ipadx=15)
        self.delete_btn.config(state='disabled')
        
        # Aktualisieren Button
        refresh_btn = self.create_button(button_frame, "🔄 Aktualisieren", 
                                        self.refresh_sticky_list, self.colors['warning'])
        refresh_btn.pack(side='right', ipady=8, ipadx=15)
    
    def refresh_sticky_list(self):
        """Aktualisiert die Liste der Sticky Messages - VERSCHLÜSSELT"""
        try:
            # Liste leeren
            self.sticky_listbox.delete(0, tk.END)
            
            # Sticky Messages über verschlüsseltes System laden
            sticky_messages = load_sticky_messages_secure(None)
            
            if not sticky_messages:
                self.sticky_listbox.insert(tk.END, "Keine Sticky Messages konfiguriert")
                self.show_empty_details()
                return
            
            # Messages in Liste einfügen
            for channel_id, data in sticky_messages.items():
                channel_name = data.get('channel_name', f'Channel {channel_id}')
                title = data.get('title', 'Unbenannt')
                display_text = f"#{channel_name} - {title}"
                self.sticky_listbox.insert(tk.END, display_text)
            
            logging.info(f"🔐 {len(sticky_messages)} Sticky Messages sicher geladen (GUI)")
            
        except Exception as e:
            logging.error(f"❌ Fehler beim sicheren Laden der Sticky Messages: {e}")
            self.sticky_listbox.insert(tk.END, f"❌ Fehler beim Laden: {str(e)}")
            self.show_empty_details()
    
    def on_sticky_select(self, event=None):
        """Wird aufgerufen wenn eine Sticky Message ausgewählt wird - VERSCHLÜSSELT"""
        selection = self.sticky_listbox.curselection()
        if not selection:
            self.current_selection = None
            self.edit_btn.config(state='disabled')
            self.delete_btn.config(state='disabled')
            self.show_empty_details()
            return
        
        try:
            # Index der Auswahl
            index = selection[0]
            
            # Sticky Messages über verschlüsseltes System laden
            sticky_messages = load_sticky_messages_secure(None)
            
            # Channel ID der ausgewählten Message finden
            channel_ids = list(sticky_messages.keys())
            if index < len(channel_ids):
                channel_id = channel_ids[index]
                self.current_selection = channel_id
                self.show_sticky_details(channel_id, sticky_messages[channel_id])
                
                # Buttons aktivieren
                self.edit_btn.config(state='normal')
                self.delete_btn.config(state='normal')
            
        except Exception as e:
            logging.error(f"❌ Fehler beim Anzeigen der Details: {e}")
            self.show_empty_details()
    
    def show_sticky_details(self, channel_id, data):
        """Zeigt die Details einer Sticky Message an"""
        # Details Frame leeren
        for widget in self.details_frame.winfo_children():
            if widget != self.details_frame.winfo_children()[0]:  # Header behalten
                widget.destroy()
        
        # Scrollbarer Container für Details
        canvas = tk.Canvas(self.details_frame, bg=self.colors['secondary'], highlightthickness=0)
        scrollbar = tk.Scrollbar(self.details_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['secondary'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Details hinzufügen
        details = [
            ("🆔 Channel ID:", channel_id),
            ("📺 Channel:", f"#{data.get('channel_name', 'Unbekannt')}"),
            ("📝 Titel:", data.get('title', 'Kein Titel')),
            ("⏱️ Verzögerung:", f"{data.get('delay', 0)} Sekunden"),
            ("📅 Erstellt:", data.get('created', 'Unbekannt')),
            ("📊 Status:", "🟢 Aktiv" if data.get('active', True) else "🔴 Inaktiv")
        ]
        
        for label, value in details:
            row_frame = tk.Frame(scrollable_frame, bg=self.colors['secondary'])
            row_frame.pack(fill='x', padx=15, pady=2)
            
            tk.Label(row_frame, text=label, font=('Segoe UI', 10, 'bold'),
                    fg=self.colors['text_secondary'], bg=self.colors['secondary']).pack(anchor='w')
            
            tk.Label(row_frame, text=str(value), font=('Segoe UI', 10),
                    fg=self.colors['text_primary'], bg=self.colors['secondary'],
                    wraplength=250).pack(anchor='w', padx=(0, 0))
        
        # Message Content
        msg_frame = tk.Frame(scrollable_frame, bg=self.colors['secondary'])
        msg_frame.pack(fill='both', expand=True, padx=15, pady=(10, 15))
        
        tk.Label(msg_frame, text="💬 Nachricht:", font=('Segoe UI', 10, 'bold'),
                fg=self.colors['text_secondary'], bg=self.colors['secondary']).pack(anchor='w')
        
        # Text Widget für Nachricht
        message_text = tk.Text(msg_frame, height=8, font=('Segoe UI', 9),
                              bg='#40444B', fg='#DCDDDE', relief='flat',
                              wrap=tk.WORD, state='normal')
        message_text.pack(fill='both', expand=True, pady=(5, 0))
        
        # Nachricht einfügen
        message_content = data.get('message', 'Keine Nachricht verfügbar')
        message_text.insert('1.0', message_content)
        message_text.config(state='disabled')  # Read-only
        
        # Canvas und Scrollbar packen
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def show_empty_details(self):
        """Zeigt leere Details an"""
        # Details Frame leeren (außer Header)
        for widget in self.details_frame.winfo_children():
            if widget != self.details_frame.winfo_children()[0]:  # Header behalten
                widget.destroy()
        
        # Placeholder
        placeholder = tk.Label(self.details_frame,
                              text="📄 Wähle eine Sticky Message\n"
                                   "aus der Liste aus, um\n"
                                   "Details anzuzeigen.\n\n"
                                   "💡 Doppelklick zum Bearbeiten",
                              font=('Segoe UI', 11),
                              fg=self.colors['text_secondary'],
                              bg=self.colors['secondary'],
                              justify='center')
        placeholder.pack(expand=True)
    
    def create_new_sticky(self):
        """Öffnet den Dialog zum Erstellen einer neuen Sticky Message"""
        try:
            # Prüfe ob Bot verfügbar ist
            if not (hasattr(self.main_window, 'bot_manager') and 
                    self.main_window.bot_manager and 
                    self.main_window.bot_manager.bot):
                messagebox.showerror("Bot nicht verfügbar", 
                                   "Der Discord Bot ist nicht gestartet.\n"
                                   "Bitte starte zuerst den Bot im Status-Tab.")
                return
            
            # StickyManagerDialog öffnen
            dialog = StickyManagerDialog(self.main_window, self.main_window.bot_manager.bot)
            
            # Nach dem Dialog die Liste aktualisieren
            self.main_window.root.after(100, self.refresh_sticky_list)
            
        except Exception as e:
            logging.error(f"❌ Fehler beim Öffnen des Dialogs: {e}")
            messagebox.showerror("Fehler", f"Fehler beim Öffnen des Dialogs:\n{str(e)}")
    
    def edit_sticky(self, event=None):
        """Bearbeitet die ausgewählte Sticky Message"""
        if not self.current_selection:
            messagebox.showwarning("Keine Auswahl", "Bitte wähle eine Sticky Message aus der Liste aus.")
            return
        
        try:
            # Daten der ausgewählten Message laden
            sticky_messages = load_sticky_messages_secure(None)
            
            if self.current_selection not in sticky_messages:
                messagebox.showerror("Fehler", "Die ausgewählte Sticky Message existiert nicht mehr.")
                self.refresh_sticky_list()
                return
            
            data = sticky_messages[self.current_selection]
            
            # Edit Dialog öffnen
            self.open_edit_dialog(self.current_selection, data)
            
        except Exception as e:
            logging.error(f"❌ Fehler beim Bearbeiten: {e}")
            messagebox.showerror("Fehler", f"Fehler beim Bearbeiten:\n{str(e)}")
    
    def open_edit_dialog(self, channel_id, data):
        """Öffnet den Bearbeitungs-Dialog"""
        # Neues Fenster für Bearbeitung
        edit_window = tk.Toplevel(self.main_window.root)
        edit_window.title(f"✏️ Sticky Message bearbeiten - #{data.get('channel_name', 'Unbekannt')}")
        edit_window.geometry("500x550")
        edit_window.resizable(False, False)
        edit_window.configure(bg=self.colors['background'])
        edit_window.transient(self.main_window.root)
        edit_window.grab_set()
        
        # Icon setzen
        try:
            edit_window.iconbitmap('icon.ico')
        except:
            pass
        
        # Header
        header_frame = tk.Frame(edit_window, bg=self.colors['primary'], relief='flat')
        header_frame.pack(fill='x', pady=(0, 20))
        
        header_label = tk.Label(header_frame, 
                               text=f"✏️ Bearbeiten: #{data.get('channel_name', 'Unbekannt')}", 
                               font=('Segoe UI', 16, 'bold'),
                               fg='white', bg=self.colors['primary'])
        header_label.pack(pady=15)
        
        # Main Frame
        main_frame = tk.Frame(edit_window, bg=self.colors['background'])
        main_frame.pack(fill='both', expand=True, padx=20)
        
        # Titel
        tk.Label(main_frame, text="📝 Titel:", font=('Segoe UI', 11, 'bold'),
                fg=self.colors['text_primary'], bg=self.colors['background']).pack(anchor='w', pady=(0, 5))
        
        title_entry = tk.Entry(main_frame, font=('Segoe UI', 10), 
                              bg='#40444B', fg='#DCDDDE', insertbackground='#FFFFFF')
        title_entry.pack(fill='x', ipady=5, pady=(0, 15))
        title_entry.insert(0, data.get('title', ''))
        
        # Nachricht
        tk.Label(main_frame, text="💬 Nachricht:", font=('Segoe UI', 11, 'bold'),
                fg=self.colors['text_primary'], bg=self.colors['background']).pack(anchor='w', pady=(0, 5))
        
        message_text = tk.Text(main_frame, height=10, font=('Segoe UI', 10),
                              bg='#40444B', fg='#DCDDDE', insertbackground='#FFFFFF',
                              wrap=tk.WORD)
        message_text.pack(fill='both', expand=True, pady=(0, 15))
        message_text.insert('1.0', data.get('message', ''))
        
        # Verzögerung
        tk.Label(main_frame, text="⏱️ Verzögerung (Sekunden):", font=('Segoe UI', 11, 'bold'),
                fg=self.colors['text_primary'], bg=self.colors['background']).pack(anchor='w', pady=(0, 5))
        
        delay_entry = tk.Entry(main_frame, font=('Segoe UI', 10), 
                              bg='#40444B', fg='#DCDDDE', insertbackground='#FFFFFF')
        delay_entry.pack(fill='x', ipady=5, pady=(0, 20))
        delay_entry.insert(0, str(data.get('delay', 20)))
        
        # Buttons
        button_frame = tk.Frame(main_frame, bg=self.colors['background'])
        button_frame.pack(fill='x', pady=(0, 20))
        
        def save_changes():
            try:
                # Validierung
                if not title_entry.get().strip():
                    messagebox.showerror("Fehler", "Bitte gib einen Titel ein!")
                    return
                    
                if not message_text.get("1.0", tk.END).strip():
                    messagebox.showerror("Fehler", "Bitte gib eine Nachricht ein!")
                    return
                
                try:
                    delay = int(delay_entry.get())
                    if delay < 5:
                        messagebox.showerror("Fehler", "Verzögerung muss mindestens 5 Sekunden sein!")
                        return
                except ValueError:
                    messagebox.showerror("Fehler", "Bitte gib eine gültige Zahl für die Verzögerung ein!")
                    return
                
                # Daten aktualisieren
                sticky_messages = load_sticky_messages_secure(None)
                
                sticky_messages[channel_id].update({
                    'title': title_entry.get().strip(),
                    'message': message_text.get("1.0", tk.END).strip(),
                    'delay': delay,
                    'last_modified': datetime.now().isoformat()
                })
                
                # Sicher speichern
                save_sticky_messages_secure(sticky_messages, None)
                
                messagebox.showinfo("Erfolg", "Sticky Message wurde erfolgreich aktualisiert!")
                edit_window.destroy()
                self.refresh_sticky_list()  # Liste aktualisieren
                
            except Exception as e:
                logging.error(f"❌ Fehler beim Speichern: {e}")
                messagebox.showerror("Fehler", f"Fehler beim Speichern:\n{str(e)}")
        
        cancel_btn = tk.Button(button_frame, text="❌ Abbrechen", 
                              command=edit_window.destroy, font=('Segoe UI', 10, 'bold'),
                              bg='#4F545C', fg='#FFFFFF', relief='flat', cursor='hand2')
        cancel_btn.pack(side='left', ipady=8, ipadx=15)
        
        save_btn = tk.Button(button_frame, text="💾 Speichern", 
                            command=save_changes, font=('Segoe UI', 10, 'bold'),
                            bg=self.colors['success'], fg='#FFFFFF', relief='flat', cursor='hand2')
        save_btn.pack(side='right', ipady=8, ipadx=15)
    
    def delete_sticky(self):
        """Löscht die ausgewählte Sticky Message"""
        if not self.current_selection:
            messagebox.showwarning("Keine Auswahl", "Bitte wähle eine Sticky Message aus der Liste aus.")
            return
        
        try:
            # Bestätigung
            sticky_messages = load_sticky_messages_secure(None)
            
            if self.current_selection not in sticky_messages:
                messagebox.showerror("Fehler", "Die ausgewählte Sticky Message existiert nicht mehr.")
                self.refresh_sticky_list()
                return
            
            data = sticky_messages[self.current_selection]
            channel_name = data.get('channel_name', 'Unbekannt')
            title = data.get('title', 'Unbenannt')
            
            result = messagebox.askyesno("🗑️ Sticky Message löschen?", 
                                       f"Möchtest du die Sticky Message wirklich löschen?\n\n"
                                       f"Channel: #{channel_name}\n"
                                       f"Titel: {title}\n\n"
                                       f"Diese Aktion kann nicht rückgängig gemacht werden!")
            
            if result:
                # Aus Datei entfernen
                del sticky_messages[self.current_selection]
                
                # Datei speichern
                save_sticky_messages_secure(sticky_messages, None)
                
                messagebox.showinfo("Erfolg", f"Sticky Message für #{channel_name} wurde gelöscht!")
                
                # GUI aktualisieren
                self.current_selection = None
                self.edit_btn.config(state='disabled')
                self.delete_btn.config(state='disabled')
                self.refresh_sticky_list()
                self.show_empty_details()
                
        except Exception as e:
            logging.error(f"❌ Fehler beim Löschen: {e}")
            messagebox.showerror("Fehler", f"Fehler beim Löschen:\n{str(e)}") 