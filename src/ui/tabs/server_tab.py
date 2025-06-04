"""
Server Verwaltung Tab - Vollständige Implementierung
"""
import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
import os
import json
import logging

from src.ui.tabs.base_tab import BaseTab
from src.utils.path_manager import get_application_path
from src.utils.permissions import load_permissions, save_permissions, is_bot_admin, is_bot_editor


class ServerTab(BaseTab):
    def __init__(self, parent_frame, main_window):
        self.server_tree = None
        self.selected_server = None
        self.permission_widgets = {}
        super().__init__(parent_frame, main_window)
        
    def setup_ui(self):
        """Setup des Server Tab UI - Sicherheitsorientiert"""
        # Header
        self.create_header("🔐 Meine Server & Berechtigungen", self.colors['warning'])
        
        # Sicherheitsinfo
        security_info = tk.Frame(self.frame, bg=self.colors['background'])
        security_info.pack(fill='x', padx=10, pady=(0, 10))
        
        info_text = tk.Label(security_info,
                            text="🛡️ Sicherheit: Nur Server mit deinen Bot-Berechtigungen werden angezeigt",
                            font=('Segoe UI', 10, 'italic'),
                            fg=self.colors['success'],
                            bg=self.colors['background'])
        info_text.pack()
        
        # Main Container
        main_container = tk.Frame(self.frame, bg=self.colors['background'])
        main_container.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Linkes Panel - Server Liste
        self.setup_server_list(main_container)
        
        # Rechtes Panel - Berechtigungen
        self.setup_permissions_panel(main_container)
        
        # Button Frame
        self.setup_action_buttons()
        
        # Initial laden
        self.refresh_server_list()
        
    def setup_server_list(self, parent):
        """Setup der Server-Liste - Nur autorisierte Server"""
        left_frame = tk.Frame(parent, bg=self.colors['secondary'], relief='flat')
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        # Header
        server_header = tk.Label(left_frame,
                                text="🔐 Meine berechtigten Discord Server",
                                font=('Segoe UI', 12, 'bold'),
                                fg=self.colors['text_primary'],
                                bg=self.colors['secondary'])
        server_header.pack(pady=(10, 5))
        
        # Sicherheitshinweis
        security_note = tk.Label(left_frame,
                                text="Nur Server wo du Bot Master/Editor bist",
                                font=('Segoe UI', 9, 'italic'),
                                fg=self.colors['text_secondary'],
                                bg=self.colors['secondary'])
        security_note.pack(pady=(0, 10))
        
        # Treeview für Server
        tree_frame = tk.Frame(left_frame, bg=self.colors['secondary'])
        tree_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Scrollbar
        tree_scroll = tk.Scrollbar(tree_frame)
        tree_scroll.pack(side='right', fill='y')
        
        # Treeview mit korrigierter Konfiguration - ALLE Spalten in columns definieren
        self.server_tree = ttk.Treeview(tree_frame,
                                       columns=('server_name', 'members', 'status'),
                                       show='headings',  # REPARIERT: show nur headings, kein tree
                                       yscrollcommand=tree_scroll.set)
        self.server_tree.pack(side='left', fill='both', expand=True)
        tree_scroll.config(command=self.server_tree.yview)
        
        # REPARIERT: Spalten konfigurieren - alle definierten Spalten
        self.server_tree.heading('server_name', text='Server Name', anchor='w')
        self.server_tree.heading('members', text='Mitglieder', anchor='center')
        self.server_tree.heading('status', text='Deine Rolle & Status', anchor='center')
        
        self.server_tree.column('server_name', width=200, minwidth=150, anchor='w')
        self.server_tree.column('members', width=80, minwidth=60, anchor='center')
        self.server_tree.column('status', width=150, minwidth=120, anchor='center')
        
        # Event Handler
        self.server_tree.bind('<<TreeviewSelect>>', self.on_server_select)
        
    def setup_permissions_panel(self, parent):
        """Setup des Berechtigungs-Panels"""
        self.perm_frame = tk.Frame(parent, bg=self.colors['secondary'], relief='flat')
        self.perm_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))
        
        # Header
        perm_header = tk.Label(self.perm_frame,
                              text="🔐 Bot Berechtigungen",
                              font=('Segoe UI', 12, 'bold'),
                              fg=self.colors['text_primary'],
                              bg=self.colors['secondary'])
        perm_header.pack(pady=(10, 15))
        
        # Placeholder anzeigen
        self.show_empty_permissions()
        
    def setup_action_buttons(self):
        """Setup der Aktions-Buttons - Sicherheitsorientiert"""
        button_frame = tk.Frame(self.frame, bg=self.colors['background'])
        button_frame.pack(fill='x', padx=10, pady=(10, 0))
        
        # Info Label
        action_info = tk.Label(button_frame,
                              text="🔐 Aktionen nur auf Servern mit Bot Master Berechtigung verfügbar",
                              font=('Segoe UI', 9, 'italic'),
                              fg=self.colors['text_secondary'],
                              bg=self.colors['background'])
        action_info.pack(pady=(0, 10))
        
        # Buttons Container
        buttons_container = tk.Frame(button_frame, bg=self.colors['background'])
        buttons_container.pack(fill='x')
        
        # Server aktualisieren
        refresh_btn = self.create_button(buttons_container, "🔄 Meine Server aktualisieren", 
                                        self.refresh_server_list, self.colors['primary'])
        refresh_btn.pack(side='left', ipady=8, ipadx=15)
        
        # Benutzer hinzufügen (nur Bot Master)
        self.add_user_btn = self.create_button(buttons_container, "👤 Bot Master hinzufügen", 
                                              self.add_bot_master, self.colors['success'])
        self.add_user_btn.pack(side='left', padx=(10, 0), ipady=8, ipadx=15)
        self.add_user_btn.config(state='disabled')
        
        # Editor hinzufügen (nur Bot Master)
        self.add_editor_btn = self.create_button(buttons_container, "✏️ Bot Editor hinzufügen", 
                                                 self.add_bot_editor, self.colors['warning'])
        self.add_editor_btn.pack(side='left', padx=(10, 0), ipady=8, ipadx=15)
        self.add_editor_btn.config(state='disabled')
        
        # Berechtigungen exportieren
        export_btn = self.create_button(buttons_container, "📄 Meine Berechtigungen exportieren", 
                                       self.export_permissions, '#4F545C')
        export_btn.pack(side='right', ipady=8, ipadx=15)
        
    def refresh_server_list(self):
        """Aktualisiert die Server-Liste - NUR Server mit Berechtigungen für authentifizierten User"""
        try:
            # Tree leeren
            for item in self.server_tree.get_children():
                self.server_tree.delete(item)
            
            # Authentifizierung prüfen
            if not hasattr(self.main_window, 'authenticated_user_id') or not self.main_window.authenticated_user_id:
                self.server_tree.insert('', 'end', iid=None, 
                                       values=("🔐 Authentifizierung erforderlich", "--", "Nicht angemeldet"))
                self.show_empty_permissions()
                logging.info("🔐 Server-Liste: Authentifizierung erforderlich")
                return
            
            # Bot prüfen
            if not (hasattr(self.main_window, 'bot_manager') and 
                    self.main_window.bot_manager and 
                    self.main_window.bot_manager.bot):
                self.server_tree.insert('', 'end', iid=None, 
                                       values=("❌ Bot nicht gestartet", "--", "Offline"))
                self.show_empty_permissions()
                return
            
            bot = self.main_window.bot_manager.bot
            if not bot.guilds:
                self.server_tree.insert('', 'end', iid=None,
                                       values=("📭 Keine Server verbunden", "--", "Keine Daten"))
                self.show_empty_permissions()
                return
            
            # Berechtigungen laden
            permissions = load_permissions()
            authenticated_user_str = str(self.main_window.authenticated_user_id)
            
            # NUR Server mit Berechtigungen für authentifizierten User
            authorized_servers = []
            
            for guild in bot.guilds:
                guild_str = str(guild.id)
                guild_perms = permissions.get(guild_str, {})
                
                # Prüfe ob User Bot Master oder Editor ist
                is_master = authenticated_user_str in guild_perms.get('masters', [])
                is_editor = authenticated_user_str in guild_perms.get('editors', [])
                
                if is_master or is_editor:
                    authorized_servers.append({
                        'guild': guild,
                        'is_master': is_master,
                        'is_editor': is_editor,
                        'guild_perms': guild_perms
                    })
            
            # Keine autorisierten Server
            if not authorized_servers:
                self.server_tree.insert('', 'end', iid=None,
                                       values=("🚫 Keine berechtigten Server", "--", "Zugriff verweigert"))
                self.show_empty_permissions()
                logging.info(f"🔐 User {authenticated_user_str}: Keine berechtigten Server gefunden")
                return
            
            # Autorisierte Server hinzufügen
            for server_info in authorized_servers:
                guild = server_info['guild']
                guild_perms = server_info['guild_perms']
                is_master = server_info['is_master']
                is_editor = server_info['is_editor']
                
                # Rolle bestimmen
                if is_master:
                    user_role = "👑 Bot Master"
                elif is_editor:
                    user_role = "✏️ Bot Editor"
                else:
                    continue  # Sollte nicht vorkommen
                
                # Gesamtanzahl für Status
                masters_count = len(guild_perms.get('masters', []))
                editors_count = len(guild_perms.get('editors', []))
                status = f"{user_role} | {masters_count}M/{editors_count}E"
                
                # In Tree einfügen
                item_id = f"guild_{guild.id}"
                self.server_tree.insert('', 'end', iid=item_id,
                                      values=(f"🏠 {guild.name}", f"{guild.member_count}", status))
                
            logging.info(f"🔐 User {authenticated_user_str}: {len(authorized_servers)} berechtigte Server geladen")
            
        except Exception as e:
            logging.error(f"❌ Fehler beim Laden der Server: {e}")
            self.server_tree.insert('', 'end', iid=None,
                                   values=(f"❌ Fehler: {str(e)}", "--", "Fehler"))
            
    def on_server_select(self, event=None):
        """Wird aufgerufen wenn ein Server ausgewählt wird - mit Sicherheitsprüfung"""
        selection = self.server_tree.selection()
        if not selection:
            self.selected_server = None
            self.add_user_btn.config(state='disabled')
            self.add_editor_btn.config(state='disabled')
            self.show_empty_permissions()
            return
        
        try:
            # Authentifizierung prüfen
            if not hasattr(self.main_window, 'authenticated_user_id') or not self.main_window.authenticated_user_id:
                logging.warning("🔐 Server-Auswahl ohne Authentifizierung blockiert")
                self.show_empty_permissions()
                return
            
            # Server Item
            item = selection[0]
            # REPARIERT: Hole Server-Name aus values statt text
            item_values = self.server_tree.item(item, 'values')
            if not item_values or len(item_values) < 1:
                return
                
            server_name_with_icon = item_values[0]  # "🏠 ServerName"
            server_name = server_name_with_icon.replace("🏠 ", "")  # Entferne Icon
            
            # Bot prüfen
            if not (hasattr(self.main_window, 'bot_manager') and 
                    self.main_window.bot_manager and 
                    self.main_window.bot_manager.bot):
                return
            
            # Guild finden
            bot = self.main_window.bot_manager.bot
            guild = None
            for g in bot.guilds:
                if g.name == server_name:
                    guild = g
                    break
            
            if guild:
                # SICHERHEITSPRÜFUNG: User muss berechtigt sein
                permissions = load_permissions()
                authenticated_user_str = str(self.main_window.authenticated_user_id)
                guild_str = str(guild.id)
                guild_perms = permissions.get(guild_str, {})
                
                is_master = authenticated_user_str in guild_perms.get('masters', [])
                is_editor = authenticated_user_str in guild_perms.get('editors', [])
                
                if is_master or is_editor:
                    self.selected_server = guild
                    self.show_server_permissions(guild)
                    
                    # Buttons nur für Bot Master aktivieren
                    if is_master:
                        self.add_user_btn.config(state='normal')
                        self.add_editor_btn.config(state='normal')
                    else:
                        # Editor kann nur anzeigen, nicht ändern
                        self.add_user_btn.config(state='disabled')
                        self.add_editor_btn.config(state='disabled')
                        
                    logging.info(f"🔐 Server ausgewählt: {guild.name} (User: {'Master' if is_master else 'Editor'})")
                else:
                    # Nicht autorisiert - sollte nicht passieren da Server gefiltert sind
                    logging.warning(f"🔐 Unerlaubter Zugriff auf Server {guild.name} blockiert")
                    self.selected_server = None
                    self.show_empty_permissions()
            else:
                self.selected_server = None
                self.show_empty_permissions()
                
        except Exception as e:
            logging.error(f"❌ Fehler bei Server-Auswahl: {e}")
            self.show_empty_permissions()
    
    def show_server_permissions(self, guild):
        """Zeigt die Berechtigungen für einen Server"""
        # Panel leeren (außer Header)
        for widget in self.perm_frame.winfo_children():
            if widget != self.perm_frame.winfo_children()[0]:
                widget.destroy()
        
        # Server Info
        info_frame = tk.Frame(self.perm_frame, bg=self.colors['secondary'])
        info_frame.pack(fill='x', padx=15, pady=(0, 15))
        
        tk.Label(info_frame, text=f"🏠 {guild.name}",
                font=('Segoe UI', 14, 'bold'),
                fg=self.colors['text_primary'],
                bg=self.colors['secondary']).pack(anchor='w')
        
        tk.Label(info_frame, text=f"ID: {guild.id} | Mitglieder: {guild.member_count}",
                font=('Segoe UI', 9),
                fg=self.colors['text_secondary'],
                bg=self.colors['secondary']).pack(anchor='w')
        
        # Scrollbarer Container
        canvas = tk.Canvas(self.perm_frame, bg=self.colors['secondary'], highlightthickness=0)
        scrollbar = tk.Scrollbar(self.perm_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['secondary'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Berechtigungen laden
        permissions = load_permissions()
        guild_str = str(guild.id)
        guild_perms = permissions.get(guild_str, {'masters': [], 'editors': []})
        
        # Bot Masters Sektion
        masters_frame = tk.Frame(scrollable_frame, bg='#4F545C', relief='flat')
        masters_frame.pack(fill='x', padx=15, pady=(0, 10))
        
        tk.Label(masters_frame, text="👑 Bot Masters (Vollzugriff)",
                font=('Segoe UI', 11, 'bold'),
                fg='#FFD700', bg='#4F545C').pack(pady=8)
        
        masters = guild_perms.get('masters', [])
        if masters:
            for user_id in masters:
                self.create_user_row(masters_frame, user_id, 'master', guild_str)
        else:
            tk.Label(masters_frame, text="Keine Bot Masters konfiguriert",
                    font=('Segoe UI', 9, 'italic'),
                    fg=self.colors['text_secondary'], bg='#4F545C').pack(pady=5)
        
        # Bot Editors Sektion
        editors_frame = tk.Frame(scrollable_frame, bg='#40444B', relief='flat')
        editors_frame.pack(fill='x', padx=15, pady=(0, 15))
        
        tk.Label(editors_frame, text="✏️ Bot Editors (Sticky Messages)",
                font=('Segoe UI', 11, 'bold'),
                fg='#00b894', bg='#40444B').pack(pady=8)
        
        editors = guild_perms.get('editors', [])
        if editors:
            for user_id in editors:
                self.create_user_row(editors_frame, user_id, 'editor', guild_str)
        else:
            tk.Label(editors_frame, text="Keine Bot Editors konfiguriert",
                    font=('Segoe UI', 9, 'italic'),
                    fg=self.colors['text_secondary'], bg='#40444B').pack(pady=5)
        
        # Canvas packen
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def create_user_row(self, parent, user_id, role, guild_str):
        """Erstellt eine Zeile für einen Benutzer"""
        row_frame = tk.Frame(parent, bg=parent['bg'])
        row_frame.pack(fill='x', padx=10, pady=2)
        
        # User Info
        user_info = f"👤 {user_id}"
        # Versuche Discord Username zu finden (falls Bot läuft)
        try:
            if (hasattr(self.main_window, 'bot_manager') and 
                self.main_window.bot_manager and 
                self.main_window.bot_manager.bot):
                user = self.main_window.bot_manager.bot.get_user(int(user_id))
                if user:
                    user_info = f"👤 {user.display_name} ({user_id})"
        except:
            pass
        
        tk.Label(row_frame, text=user_info,
                font=('Segoe UI', 9),
                fg=self.colors['text_primary'],
                bg=parent['bg']).pack(side='left')
        
        # Remove Button
        remove_btn = tk.Button(row_frame, text="❌",
                              command=lambda: self.remove_user(user_id, role, guild_str),
                              font=('Segoe UI', 8),
                              bg=self.colors['error'],
                              fg='white',
                              relief='flat',
                              cursor='hand2',
                              bd=0)
        remove_btn.pack(side='right', padx=(5, 0))
        
    def show_empty_permissions(self):
        """Zeigt leere Berechtigungen an"""
        # Panel leeren (außer Header)
        for widget in self.perm_frame.winfo_children():
            if widget != self.perm_frame.winfo_children()[0]:
                widget.destroy()
        
        placeholder = tk.Label(self.perm_frame,
                              text="🔐 Wähle einen Server aus\n"
                                   "der Liste aus, um\n"
                                   "Berechtigungen zu verwalten.\n\n"
                                   "💡 Bot Masters haben Vollzugriff\n"
                                   "Bot Editors können nur\n"
                                   "Sticky Messages verwalten",
                              font=('Segoe UI', 11),
                              fg=self.colors['text_secondary'],
                              bg=self.colors['secondary'],
                              justify='center')
        placeholder.pack(expand=True)
        
    def add_bot_master(self):
        """Fügt einen Bot Master hinzu"""
        if not self.selected_server:
            messagebox.showwarning("Kein Server", "Bitte wähle einen Server aus der Liste aus.")
            return
        
        self.add_user_dialog("Bot Master", "master")
        
    def add_bot_editor(self):
        """Fügt einen Bot Editor hinzu"""
        if not self.selected_server:
            messagebox.showwarning("Kein Server", "Bitte wähle einen Server aus der Liste aus.")
            return
        
        self.add_user_dialog("Bot Editor", "editor")
        
    def add_user_dialog(self, role_name, role_type):
        """Zeigt Dialog zum Hinzufügen eines Benutzers"""
        user_id = simpledialog.askstring(
            f"{role_name} hinzufügen",
            f"Discord User-ID für neuen {role_name} eingeben:\n\n"
            f"So findest du die User-ID:\n"
            f"1. Discord → Einstellungen → Erweitert\n"
            f"2. 'Entwicklermodus' aktivieren\n"
            f"3. Rechtsklick auf Benutzer → 'ID kopieren'\n\n"
            f"User-ID:",
            parent=self.main_window.root
        )
        
        if not user_id:
            return
            
        # Validierung
        if not user_id.isdigit() or len(user_id) < 17:
            messagebox.showerror("Ungültige ID", "Bitte gib eine gültige Discord User-ID ein!")
            return
        
        try:
            # Berechtigungen laden
            permissions = load_permissions()
            guild_str = str(self.selected_server.id)
            
            # Guild erstellen falls nicht vorhanden
            if guild_str not in permissions:
                permissions[guild_str] = {'masters': [], 'editors': []}
            
            # Prüfen ob User bereits existiert
            if user_id in permissions[guild_str].get('masters', []):
                messagebox.showwarning("Bereits vorhanden", 
                                     f"User {user_id} ist bereits Bot Master auf diesem Server!")
                return
                
            if user_id in permissions[guild_str].get('editors', []):
                if role_type == 'editor':
                    messagebox.showwarning("Bereits vorhanden", 
                                         f"User {user_id} ist bereits Bot Editor auf diesem Server!")
                    return
                else:
                    # Von Editor zu Master upgraden
                    permissions[guild_str]['editors'].remove(user_id)
            
            # User hinzufügen
            role_key = 'masters' if role_type == 'master' else 'editors'
            permissions[guild_str][role_key].append(user_id)
            
            # Speichern
            save_permissions(permissions)
            
            messagebox.showinfo("Erfolg", 
                              f"User {user_id} wurde als {role_name} hinzugefügt!")
            
            # Anzeige aktualisieren
            self.show_server_permissions(self.selected_server)
            self.refresh_server_list()  # Status in Liste aktualisieren
            
        except Exception as e:
            logging.error(f"❌ Fehler beim Hinzufügen des Users: {e}")
            messagebox.showerror("Fehler", f"Fehler beim Hinzufügen:\n{str(e)}")
    
    def remove_user(self, user_id, role, guild_str):
        """Entfernt einen Benutzer"""
        try:
            role_name = "Bot Master" if role == "master" else "Bot Editor"
            
            result = messagebox.askyesno("Benutzer entfernen?",
                                       f"Möchtest du User {user_id} wirklich\n"
                                       f"als {role_name} entfernen?\n\n"
                                       f"Server: {self.selected_server.name}")
            
            if result:
                # Berechtigungen laden
                permissions = load_permissions()
                
                # User entfernen
                role_key = 'masters' if role == 'master' else 'editors'
                if (guild_str in permissions and 
                    user_id in permissions[guild_str].get(role_key, [])):
                    permissions[guild_str][role_key].remove(user_id)
                    
                    # Speichern
                    save_permissions(permissions)
                    
                    messagebox.showinfo("Erfolg", f"User {user_id} wurde entfernt!")
                    
                    # Anzeige aktualisieren
                    self.show_server_permissions(self.selected_server)
                    self.refresh_server_list()
                else:
                    messagebox.showerror("Fehler", "User nicht gefunden!")
                    
        except Exception as e:
            logging.error(f"❌ Fehler beim Entfernen: {e}")
            messagebox.showerror("Fehler", f"Fehler beim Entfernen:\n{str(e)}")
    
    def export_permissions(self):
        """Exportiert die Berechtigungen"""
        try:
            permissions = load_permissions()
            
            # Formatierte Ausgabe erstellen
            export_text = "=== STICKY-BOT BERECHTIGUNGEN ===\n\n"
            
            if not permissions:
                export_text += "Keine Berechtigungen konfiguriert.\n"
            else:
                for guild_str, perms in permissions.items():
                    # Guild Name finden
                    guild_name = guild_str
                    if (hasattr(self.main_window, 'bot_manager') and 
                        self.main_window.bot_manager and 
                        self.main_window.bot_manager.bot):
                        guild = self.main_window.bot_manager.bot.get_guild(int(guild_str))
                        if guild:
                            guild_name = f"{guild.name} ({guild_str})"
                    
                    export_text += f"🏠 Server: {guild_name}\n"
                    
                    masters = perms.get('masters', [])
                    if masters:
                        export_text += f"  👑 Bot Masters ({len(masters)}):\n"
                        for user_id in masters:
                            export_text += f"    - {user_id}\n"
                    else:
                        export_text += "  👑 Bot Masters: Keine\n"
                    
                    editors = perms.get('editors', [])
                    if editors:
                        export_text += f"  ✏️ Bot Editors ({len(editors)}):\n"
                        for user_id in editors:
                            export_text += f"    - {user_id}\n"
                    else:
                        export_text += "  ✏️ Bot Editors: Keine\n"
                    
                    export_text += "\n"
            
            # Export Dialog
            export_window = tk.Toplevel(self.main_window.root)
            export_window.title("📄 Berechtigungen Export")
            export_window.geometry("600x500")
            export_window.configure(bg=self.colors['background'])
            export_window.transient(self.main_window.root)
            
            # Header
            header = tk.Label(export_window, text="📄 Berechtigungen Export",
                             font=('Segoe UI', 16, 'bold'),
                             fg=self.colors['text_primary'],
                             bg=self.colors['background'])
            header.pack(pady=15)
            
            # Text Widget
            text_widget = tk.Text(export_window, font=('Consolas', 10),
                                 bg='#40444B', fg='#DCDDDE',
                                 wrap=tk.WORD, relief='flat')
            text_widget.pack(fill='both', expand=True, padx=20, pady=(0, 15))
            text_widget.insert('1.0', export_text)
            text_widget.config(state='disabled')
            
            # Close Button
            close_btn = tk.Button(export_window, text="❌ Schließen",
                                 command=export_window.destroy,
                                 font=('Segoe UI', 11, 'bold'),
                                 bg='#4F545C', fg='white',
                                 relief='flat', cursor='hand2')
            close_btn.pack(pady=(0, 15))
            
        except Exception as e:
            logging.error(f"❌ Fehler beim Export: {e}")
            messagebox.showerror("Export Fehler", f"Fehler beim Export:\n{str(e)}") 