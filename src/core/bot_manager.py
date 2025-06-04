"""
Discord Bot Management
Behandelt Bot-Setup, Token-Management und Event-Handling
"""
import discord
from discord.ext import commands
import asyncio
import logging
import os
import sys
import traceback
import threading
from datetime import datetime

from src.config.constants import INITIAL_EXTENSIONS
from src.utils.path_manager import get_application_path
from src.utils.logging_setup import safe_print

# Liste der zu ladenden Extensions
INITIAL_EXTENSIONS = [
    'src.cogs.sticky',
    'src.cogs.admin'
]

class BotManager:
    def __init__(self, status_window=None):
        self.status_window = status_window
        self.bot = None
        self.bot_running = False
        self.bot_thread = None
        self.token = None
        
    def setup_bot(self):
        """Initialisiert den Discord Bot"""
        try:
            intents = discord.Intents.default()
            intents.message_content = True
            self.bot = commands.Bot(command_prefix='/', intents=intents)
            
            # Event Handlers registrieren
            self.register_event_handlers()
            
            return True
            
        except Exception as e:
            logging.error(f"Bot Initialisierung fehlgeschlagen: {e}")
            logging.error(traceback.format_exc())
            safe_print(f"❌ Bot Initialisierung fehlgeschlagen: {e}")
            return False
    
    def register_event_handlers(self):
        """Registriert Bot Event Handlers"""
        @self.bot.event
        async def on_ready():
            safe_print(f"✅ Bot '{self.bot.user.name}' ist online auf {len(self.bot.guilds)} Servern!")
            
            # Berechtigungssystem initialisieren
            try:
                from src.utils.permissions import initialize_permissions_at_startup
                initialize_permissions_at_startup(self.bot)
            except Exception as perm_error:
                logging.error(f"Berechtigungssystem-Initialisierung fehlgeschlagen: {perm_error}")
            
            # Commands automatisch synchronisieren
            await self.sync_commands()
            
            # Bot Status setzen
            activity = discord.Activity(type=discord.ActivityType.watching, 
                                      name="Sticky Messages | /help")
            await self.bot.change_presence(status=discord.Status.online, activity=activity)
            
            # Status Window benachrichtigen falls vorhanden
            if self.status_window:
                self.status_window.on_bot_ready()
            
            self.bot_running = True
            
            if self.status_window:
                self.status_window.update_status(
                    f"✅ Bot online: {self.bot.user.name}",
                    f"Verbunden mit {len(self.bot.guilds)} Server(n)",
                    "#00b894"
                )
                self.status_window.add_log(f"✅ Bot erfolgreich gestartet als {self.bot.user.name}")
                self.status_window.add_log(f"📊 Verbunden mit {len(self.bot.guilds)} Discord-Server(n)")
                
                # Buttons aktualisieren (falls verfügbar)
                if hasattr(self.status_window, 'status_tab') and self.status_window.status_tab:
                    if hasattr(self.status_window.status_tab, 'start_btn'):
                        self.status_window.status_tab.start_btn.config(state='disabled')
                    if hasattr(self.status_window.status_tab, 'stop_btn'):
                        self.status_window.status_tab.stop_btn.config(state='normal')
                
                # Liste der Server anzeigen
                for guild in self.bot.guilds:
                    self.status_window.add_log(f"🏠 Server: {guild.name} ({guild.member_count} Mitglieder)")

        @self.bot.event
        async def on_disconnect():
            logging.warning("Bot wurde getrennt")
            safe_print("⚠️ Bot wurde getrennt")
            
            if self.status_window:
                self.status_window.update_status(
                    "⚠️ Bot getrennt",
                    "Verbindung zu Discord verloren",
                    "#FAA61A"
                )
                self.status_window.add_log("⚠️ Verbindung zu Discord verloren")

        @self.bot.event
        async def on_resumed():
            safe_print("🔄 Bot-Verbindung wiederhergestellt")
            
            if self.status_window:
                self.status_window.update_status(
                    f"✅ Bot online: {self.bot.user.name}",
                    "Verbindung wiederhergestellt",
                    "#00b894"
                )
                self.status_window.add_log("🔄 Verbindung zu Discord wiederhergestellt")

        @self.bot.event
        async def on_guild_join(guild):
            safe_print(f"➕ Neuer Server: {guild.name}")
            
            # Commands für neuen Server synchronisieren
            try:
                synced = await self.bot.tree.sync(guild=guild)
            except Exception as sync_error:
                logging.warning(f"Command Sync für {guild.name} fehlgeschlagen: {sync_error}")
            
            if self.status_window:
                self.status_window.refresh_server_data()
    
    def get_token(self):
        """Token aus .env laden oder Setup starten"""
        try:
            # .env Pfad relativ zum App-Pfad
            app_path = get_application_path()
            env_path = os.path.join(app_path, '.env')
            
            from dotenv import load_dotenv
            load_dotenv(env_path)
            
            # Versuche beide Token-Namen
            token = os.getenv('DISCORD_BOT_TOKEN') or os.getenv('DISCORD_TOKEN')
            
            if token and token != 'DEIN_BOT_TOKEN_HIER' and len(token) > 50:
                self.token = token
                return token
            else:
                # Token Setup starten
                from src.utils.token_setup import setup_token
                if setup_token():
                    # Nach Setup nochmal versuchen zu laden
                    load_dotenv(env_path)
                    new_token = os.getenv('DISCORD_BOT_TOKEN') or os.getenv('DISCORD_TOKEN')
                    self.token = new_token
                    return new_token
                else:
                    logging.error("Token Setup fehlgeschlagen")
                    return None
                    
        except Exception as e:
            logging.error(f"Fehler beim Token-Setup: {e}")
            logging.error(traceback.format_exc())
            return None
    
    async def load_extensions(self):
        """Lädt alle Bot Extensions/Cogs"""
        for extension in INITIAL_EXTENSIONS:
            try:
                await self.bot.load_extension(extension)
                safe_print(f'✅ Loaded extension {extension}')
            except Exception as e:
                logging.error(f'Failed to load extension {extension}: {e}')
                logging.error(traceback.format_exc())
    
    async def sync_commands(self):
        """Synchronisiert alle Bot Commands mit Discord"""
        try:
            # Global sync
            synced = await self.bot.tree.sync()
            
            # Guild-spezifische Syncs für wichtige Server
            important_guilds = []
            for guild in self.bot.guilds:
                if guild.member_count > 10:  # Nur wichtige Server
                    try:
                        guild_synced = await self.bot.tree.sync(guild=guild)
                        important_guilds.append(f"{guild.name}: {len(guild_synced)}")
                    except Exception as guild_error:
                        logging.warning(f"Sync für {guild.name} fehlgeschlagen: {guild_error}")
            
            if self.status_window:
                self.status_window.add_log(f"✅ {len(synced)} Commands global synchronisiert")
                for guild_info in important_guilds:
                    self.status_window.add_log(f"   Server: {guild_info}")
            
            return True
            
        except Exception as e:
            logging.error(f"Command Sync fehlgeschlagen: {e}")
            safe_print(f"⚠️ Command Sync Fehler: {e}")
            return False
    
    async def run_bot(self):
        """Läuft den Bot"""
        try:
            # Bot Setup falls noch nicht geschehen
            if self.bot is None:
                if not self.setup_bot():
                    raise Exception("Bot Setup fehlgeschlagen")
            
            # Token laden falls nicht vorhanden
            if not self.token:
                token = self.get_token()
                if not token:
                    raise Exception("Token konnte nicht geladen werden")
                self.token = token
            
            async with self.bot:
                await self.load_extensions()
                await self.bot.start(self.token)
                
        except discord.LoginFailure as e:
            self.bot_running = False
            
            if self.status_window:
                self.status_window.update_status(
                    "❌ Login fehlgeschlagen",
                    "Ungültiger Discord Token",
                    "#ed4245"
                )
                self.status_window.add_log("❌ Bot Login fehlgeschlagen - Token ungültig!")
                self._reset_buttons()
            
            safe_print(f"❌ Discord Login fehlgeschlagen: {e}")
            self._show_error_and_restart()
            
        except Exception as e:
            self.bot_running = False
            logging.error(f"❌ Ein unerwarteter Fehler ist aufgetreten: {e}")
            logging.error(traceback.format_exc())
            
            if self.status_window:
                self.status_window.update_status(
                    "❌ Bot Fehler",
                    f"Unerwarteter Fehler: {str(e)[:50]}",
                    "#ed4245"
                )
                self.status_window.add_log(f"❌ Bot Fehler: {str(e)}")
                self._reset_buttons()
            
            safe_print(f"❌ Ein unerwarteter Fehler ist aufgetreten: {e}")
            self._show_error_and_restart()
        
        finally:
            self.bot_running = False
            if self.status_window:
                self.status_window.update_status(
                    "⭕ Bot gestoppt",
                    "Bot wurde beendet",
                    "#FAA61A"
                )
                self._reset_buttons()
    
    def _reset_buttons(self):
        """Setzt die Buttons zurück nach einem Fehler"""
        if (self.status_window and hasattr(self.status_window, 'status_tab') 
            and self.status_window.status_tab):
            if hasattr(self.status_window.status_tab, 'start_btn'):
                self.status_window.status_tab.start_btn.config(state='normal')
            if hasattr(self.status_window.status_tab, 'stop_btn'):
                self.status_window.status_tab.stop_btn.config(state='disabled')
    
    def _show_error_and_restart(self):
        """Zeigt Fehler an und fragt nach Neustart"""
        try:
            if self.status_window:
                # GUI verfügbar - zeige Dialog
                from tkinter import messagebox
                result = messagebox.askyesno(
                    "❌ Bot Login fehlgeschlagen!", 
                    "Der Discord Bot Token ist ungültig oder falsch!\n\n"
                    "Mögliche Ursachen:\n"
                    "• Token ist abgelaufen oder wurde zurückgesetzt\n"
                    "• Token gehört nicht zu einem Bot\n"
                    "• Copy-Paste Fehler\n\n"
                    "Möchtest du einen neuen Token eingeben?\n\n"
                    "Debug-Log: sticky_bot_debug.log",
                    parent=self.status_window.root
                )
                return result
            else:
                # Fallback ohne GUI
                safe_print("\n" + "="*60)
                safe_print("❌ BOT LOGIN FEHLGESCHLAGEN!")
                safe_print("="*60)
                safe_print("Der Discord Token ist ungültig!")
                safe_print("\nMögliche Ursachen:")
                safe_print("• Token ist abgelaufen oder wurde zurückgesetzt")
                safe_print("• Token gehört nicht zu einem Bot")
                safe_print("• Copy-Paste Fehler")
                app_path = get_application_path()
                safe_print(f"\nDebug-Log: {os.path.join(app_path, 'sticky_bot_debug.log')}")
                safe_print("\nBitte starte den Bot neu für ein neues Setup.")
                safe_print("="*60)
                input("\nDrücke Enter zum Beenden...")
                return False
                
        except Exception as e:
            logging.error(f"❌ Error-Dialog Fehler: {e}")
            return False
    
    def _restart_application(self):
        """Startet die Anwendung neu"""
        # .env löschen um Setup zu erzwingen
        app_path = get_application_path()
        env_path = os.path.join(app_path, '.env')
        if os.path.exists(env_path):
            os.remove(env_path)
            logging.info("🗑️ .env Datei gelöscht")
        
        # Anwendung neu starten
        if getattr(sys, 'frozen', False):
            os.execv(sys.executable, sys.argv)
        else:
            os.execv(sys.executable, [sys.executable] + sys.argv)
    
    def start_bot_thread(self):
        """Startet den Bot in einem separaten Thread"""
        if self.bot_running:
            if self.status_window:
                self.status_window.add_log("⚠️ Bot läuft bereits!")
            return None
            
        if not self.token:
            token = self.get_token()
            if not token:
                if self.status_window:
                    self.status_window.add_log("❌ Kein gültiger Token verfügbar!")
                return None
        
        def run_async_bot():
            try:
                asyncio.run(self.run_bot())
            except KeyboardInterrupt:
                logging.info('👋 Bot wurde durch Benutzer beendet')
            except Exception as e:
                logging.error(f"❌ Bot Thread Fehler: {e}")
                if self.status_window:
                    self.status_window.add_log(f"❌ Bot Thread Fehler: {e}")
            finally:
                self.bot_running = False
                self._reset_buttons()
        
        self.bot_thread = threading.Thread(target=run_async_bot, daemon=True)
        self.bot_thread.start()
        return self.bot_thread
    
    def stop_bot(self):
        """Stoppt den Bot"""
        if not self.bot_running:
            if self.status_window:
                self.status_window.add_log("⚠️ Bot läuft nicht!")
            return
            
        if self.status_window:
            self.status_window.add_log("⏹️ Bot wird gestoppt...")
            self.status_window.update_status("⏹️ Bot wird gestoppt...", 
                                           "Verbindungen werden getrennt...", "#FAA61A")
        
        try:
            # Bot sauber beenden
            if self.bot and not self.bot.is_closed():
                asyncio.run_coroutine_threadsafe(self.bot.close(), self.bot.loop)
            
            self.bot_running = False
            
            if self.status_window:
                self.status_window.update_status("⏸️ Bot gestoppt", 
                                                "Bereit zum Starten...", "#ed4245")
                self.status_window.add_log("✅ Bot erfolgreich gestoppt")
                self._reset_buttons()
            
        except Exception as e:
            if self.status_window:
                self.status_window.add_log(f"❌ Fehler beim Stoppen: {e}")
            logging.error(f"Fehler beim Bot-Stop: {e}")
    
    def restart_bot(self):
        """Startet den Bot neu"""
        if self.status_window:
            from tkinter import messagebox
            result = messagebox.askyesno("🔄 Bot neu starten?", 
                                       "Möchtest du den Bot wirklich neu starten?\n"
                                       "Alle aktiven Verbindungen werden getrennt.",
                                       parent=self.status_window.root)
            if result:
                self.status_window.add_log("🔄 Bot wird neu gestartet...")
                self._restart_application()
        else:
            self._restart_application()
            
    def change_token(self):
        """Öffnet das Token-Setup"""
        if self.status_window:
            from tkinter import messagebox
            result = messagebox.askyesno("🔑 Token ändern?", 
                                       "Möchtest du einen neuen Discord Bot Token eingeben?\n"
                                       "Der Bot wird danach neu gestartet.",
                                       parent=self.status_window.root)
            if result:
                self._restart_application() 