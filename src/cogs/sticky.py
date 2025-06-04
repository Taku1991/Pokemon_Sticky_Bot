import discord
import random
import aiohttp
from discord import app_commands
from discord.ext import commands
from src.utils.permissions import is_bot_editor, is_bot_admin
from src.utils.secure_storage import load_sticky_messages_secure, save_sticky_messages_secure
from src.config.config import STICKY_FILE
from src.ui.modals import StickyModal
import asyncio
import datetime
import logging
import os
import json

# Logging konfigurieren
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class StickyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot_token = getattr(bot, 'token', None)  # Bot-Token für sichere Speicherung
        self.sticky_messages = load_sticky_messages_secure(self.bot_token)
        self.last_sent_time = {}
        self.last_message = {}
        self.processing_channels = set()
        self.sticky_tasks = {}

    def save_sticky_messages(self):
        """Speichert Sticky Messages verschlüsselt"""
        try:
            save_sticky_messages_secure(self.sticky_messages, self.bot_token)
            logging.info("🔐 Sticky Messages sicher gespeichert")
        except Exception as e:
            logging.error(f"❌ Fehler beim sicheren Speichern: {e}")
            # Fallback auf alte Methode
            from src.utils.db_manager import save_json_file
            save_json_file(STICKY_FILE, self.sticky_messages)
        
    def reload_sticky_messages(self):
        """Lädt Sticky Messages neu - für GUI-Kompatibilität"""
        try:
            self.sticky_messages = load_sticky_messages_secure(self.bot_token)
            logging.debug("🔐 Sticky Messages sicher geladen")
        except Exception as e:
            logging.error(f"❌ Fehler beim sicheren Laden: {e}")
            # Fallback auf alte Methode
            from src.utils.db_manager import load_json_file
            self.sticky_messages = load_json_file(STICKY_FILE, {})

    async def load_sticky_messages(self):
        """Lädt Sticky Messages beim Bot-Start - Async Wrapper"""
        try:
            self.sticky_messages = load_sticky_messages_secure(self.bot_token)
            logging.info(f"✅ {len(self.sticky_messages)} Sticky Messages geladen")
        except Exception as e:
            logging.error(f"❌ Fehler beim Laden der Sticky Messages: {e}")
            # Fallback auf alte Methode
            from src.utils.db_manager import load_json_file
            self.sticky_messages = load_json_file(STICKY_FILE, {})
            logging.info(f"✅ {len(self.sticky_messages)} Sticky Messages über Fallback geladen")

    async def get_random_pokemon_image(self):
        try:
            async with aiohttp.ClientSession() as session:
                pokemon_id = random.randint(1, 898)
                headers = {
                    'User-Agent': 'StickyBot/1.0'
                }
                
                async with session.get(f'https://pokeapi.co/api/v2/pokemon/{pokemon_id}', headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        shiny_image = (
                            data['sprites']['other']['official-artwork'].get('front_shiny') or
                            data['sprites']['other']['official-artwork'].get('front_default') or
                            data['sprites'].get('front_shiny') or
                            data['sprites'].get('front_default')
                        )
                        
                        if not shiny_image:
                            raise ValueError('Kein Artwork gefunden')

                        pokemon_name = data['name'].capitalize()
                        return {
                            'url': shiny_image,
                            'name': pokemon_name
                        }

        except Exception as e:
            logging.error(f"Fehler beim Abrufen des Pokémon-Bildes: {e}")
            return None


    @app_commands.command(name="set_sticky", description="Erstellt eine Sticky-Nachricht")
    async def set_sticky(self, interaction: discord.Interaction):
        if not (is_bot_admin(interaction.user.id, interaction.guild.id) or 
                is_bot_editor(interaction.user.id, interaction.guild.id)):
            await interaction.response.send_message(
                "Du hast keine Berechtigung für diesen Befehl!",
                ephemeral=True
            )
            return

        modal = StickyModal(self.sticky_messages)
        await interaction.response.send_modal(modal)

    @app_commands.command(name="edit_sticky", description="Bearbeitet die Sticky-Nachricht des aktuellen Kanals")
    async def edit_sticky(self, interaction: discord.Interaction):
        if not (is_bot_admin(interaction.user.id, interaction.guild.id) or 
                is_bot_editor(interaction.user.id, interaction.guild.id)):
            await interaction.response.send_message(
                "Du hast keine Berechtigung für diesen Befehl!",
                ephemeral=True
            )
            return

        channel_id = str(interaction.channel.id)
        if channel_id not in self.sticky_messages:
            await interaction.response.send_message(
                "In diesem Kanal gibt es keine Sticky-Nachricht zum Bearbeiten.",
                ephemeral=True
            )
            return

        current_sticky = self.sticky_messages[channel_id]
        modal = StickyModal(
            self.sticky_messages,
            title="Sticky Nachricht bearbeiten",
            default_title=current_sticky["title"],
            default_message=current_sticky["message"],
            default_time=current_sticky["delay"],
            default_example=current_sticky.get("example", ""), 
            default_footer=current_sticky.get("footer", "")     
        )
        await interaction.response.send_modal(modal)

    @app_commands.command(name="sticky_list", description="Zeigt alle aktiven Sticky-Nachrichten")
    async def sticky_list(self, interaction: discord.Interaction):
        if not (is_bot_admin(interaction.user.id, interaction.guild.id) or 
                is_bot_editor(interaction.user.id, interaction.guild.id)):
            await interaction.response.send_message(
                "Du hast keine Berechtigung für diesen Befehl!",
                ephemeral=True
            )
            return

        if not self.sticky_messages:
            await interaction.response.send_message("Es gibt derzeit keine aktiven Sticky-Nachrichten.")
            return

        embed = discord.Embed(
            title="Aktive Sticky-Nachrichten",
            description="Übersicht aller Kanäle mit Sticky-Nachrichten",
            color=discord.Color.green()
        )

        for channel_id, data in self.sticky_messages.items():
            channel_name = data.get("channel_name", "Unbekannter Kanal")
            delay = data.get("delay", 20)
            title = data.get("title", "Kein Titel")
            
            value = f"Titel: {title}\nVerzögerung: {delay} Sekunden"
            embed.add_field(
                name=f"#{channel_name}",
                value=value,
                inline=False
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="update_sticky_time", description="Ändert die Verzögerung einer Sticky-Nachricht")
    @app_commands.describe(seconds="Neue Verzögerung in Sekunden")
    async def update_sticky_time(self, interaction: discord.Interaction, seconds: int):
        if not (is_bot_admin(interaction.user.id, interaction.guild.id) or 
                is_bot_editor(interaction.user.id, interaction.guild.id)):
            await interaction.response.send_message(
                "Du hast keine Berechtigung für diesen Befehl!",
                ephemeral=True
            )
            return

        channel_id = str(interaction.channel.id)
        if channel_id not in self.sticky_messages:
            await interaction.response.send_message("Es gibt keine Sticky-Nachricht in diesem Kanal.")
            return

        if seconds < 5:
            await interaction.response.send_message("Die minimale Verzögerung beträgt 5 Sekunden.")
            return

        try:
            self.sticky_messages[channel_id]["delay"] = seconds
            self.save_sticky_messages()
            await interaction.response.send_message(f"Die Sticky-Zeit wurde auf {seconds} Sekunden aktualisiert!")
        except Exception as e:
            await interaction.response.send_message(f"Fehler beim Aktualisieren der Zeit: {str(e)}")

    @app_commands.command(name="remove_sticky", description="Entfernt die Sticky-Nachricht aus dem aktuellen Kanal")
    async def remove_sticky(self, interaction: discord.Interaction):
        if not (is_bot_admin(interaction.user.id, interaction.guild.id) or 
                is_bot_editor(interaction.user.id, interaction.guild.id)):
            await interaction.response.send_message(
                "Du hast keine Berechtigung für diesen Befehl!",
                ephemeral=True
            )
            return

        channel_id = str(interaction.channel.id)
        if channel_id in self.sticky_messages:
            try:
                del self.sticky_messages[channel_id]
                del self.last_sent_time[channel_id]
                if channel_id in self.last_message and self.last_message[channel_id]:
                    await self.last_message[channel_id].delete()
                del self.last_message[channel_id]
                self.save_sticky_messages()
                await interaction.response.send_message('Sticky-Nachricht erfolgreich entfernt!')
            except Exception as e:
                await interaction.response.send_message(f"Fehler beim Entfernen der Sticky-Nachricht: {str(e)}")
        else:
            await interaction.response.send_message('Keine Sticky-Nachricht für diesen Kanal gefunden.')

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        # WICHTIG: Daten neu laden für GUI-Kompatibilität
        self.reload_sticky_messages()
        
        channel_id = str(message.channel.id)
        
        if channel_id in self.sticky_messages:
            logging.info(f"🔄 Sticky Message Trigger für Channel: {channel_id}")
            
            if channel_id in self.processing_channels:
                return  # Verhindert mehrfaches Ausführen

            self.processing_channels.add(channel_id)
            try:
                # Überprüfen, ob die letzte Nachricht mindestens 30 Sekunden alt ist
                last_sent_time = self.last_sent_time.get(channel_id)
                if last_sent_time and (datetime.datetime.now() - last_sent_time).total_seconds() < 30:
                    return

                # ERST das Delay warten (alte Sticky bleibt sichtbar)
                delay = self.sticky_messages[channel_id].get("delay", 30)
                logging.info(f"⏱️ Warte {delay} Sekunden bevor neue Sticky gesendet wird...")
                await asyncio.sleep(delay)

                # DANN alte Sticky-Nachricht löschen
                old_message = None
                if channel_id in self.last_message and self.last_message[channel_id]:
                    old_message = self.last_message[channel_id]
                    logging.info(f"🔍 Alte Sticky aus Speicher: {old_message.id}")
                else:
                    logging.info(f"🔍 Keine alte Sticky im Speicher - suche in Channel...")
                    old_message = await self.find_last_sticky_message(channel_id)
                
                if old_message:
                    try:
                        logging.info(f"🔍 Versuche alte Sticky zu löschen: {old_message.id}")
                        await old_message.delete()
                        logging.info(f"🗑️ Alte Sticky Message gelöscht: {old_message.id}")
                    except discord.NotFound:
                        logging.info(f"⚠️ Alte Sticky Message bereits gelöscht oder nicht gefunden")
                    except Exception as e:
                        logging.error(f"❌ Fehler beim Löschen der alten Nachricht: {e}")
                        logging.error(f"Fehler beim Löschen der alten Nachricht: {e}")
                else:
                    logging.info(f"🔍 Keine alte Sticky Message zum Löschen gefunden")

                # Erstelle das neue Embed
                sticky_data = self.sticky_messages[channel_id]
                embed = discord.Embed(
                    title=sticky_data["title"],
                    description=sticky_data["message"],
                    color=discord.Color.blue()
                )

                if sticky_data.get("example"):
                    embed.add_field(
                        name="Weitere Infos",
                        value=sticky_data["example"],
                        inline=False
                    )

                if sticky_data.get("footer"):
                    embed.set_footer(text=sticky_data['footer'])

                # Pokemon Image abrufen und hinzufügen
                pokemon_data = await self.get_random_pokemon_image()
                if pokemon_data:
                    embed.set_thumbnail(url=pokemon_data['url'])

                # SOFORT neue Sticky-Nachricht senden
                self.last_message[channel_id] = await message.channel.send(embed=embed)
                self.last_sent_time[channel_id] = datetime.datetime.now()
                logging.info(f"✅ Neue Sticky Message gesendet")

            except Exception as e:
                logging.error(f"Fehler beim Senden der Sticky-Nachricht: {e}")
            finally:
                self.processing_channels.remove(channel_id)

    async def find_last_sticky_message(self, channel_id):
        """Findet die letzte Sticky Message des Bots in einem Channel"""
        try:
            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                return None
            
            # Suche die letzten 50 Nachrichten nach Bot-Messages mit Embeds
            async for message in channel.history(limit=50):
                if (message.author == self.bot.user and 
                    message.embeds and 
                    len(message.embeds) > 0):
                    
                    # Prüfe ob es eine Sticky Message ist (hat den richtigen Titel)
                    embed = message.embeds[0]
                    sticky_data = self.sticky_messages.get(channel_id)
                    if sticky_data and embed.title == sticky_data.get("title"):
                        logging.info(f"🔍 Letzte Sticky Message gefunden: {message.id}")
                        return message
            
            logging.info(f"🔍 Keine passende Sticky Message gefunden")
            return None
            
        except Exception as e:
            logging.error(f"❌ Fehler beim Suchen der letzten Sticky Message: {e}")
            return None

    async def handle_message_for_sticky(self, message):
        """Behandelt neue Nachrichten für Sticky Message Trigger"""
        if message.author.bot:
            return
        
        channel_id = str(message.channel.id)
        if channel_id not in self.sticky_messages:
            return
        
        sticky_config = self.sticky_messages[channel_id]
        delay = sticky_config.get('delay', 30)
        
        # Trigger für Sticky Message
        logging.info(f"🔄 Sticky Message Trigger für Channel: {channel_id}")
        
        # Alte Aufgabe abbrechen falls vorhanden
        if channel_id in self.sticky_tasks:
            self.sticky_tasks[channel_id].cancel()
        
        # Neue Aufgabe erstellen
        self.sticky_tasks[channel_id] = asyncio.create_task(
            self._send_sticky_after_delay(message.channel, delay)
        )

    async def _send_sticky_after_delay(self, channel, delay):
        """Sendet Sticky Message nach Verzögerung"""
        try:
            await asyncio.sleep(delay)
            
            channel_id = str(channel.id)
            if channel_id not in self.sticky_messages:
                return
            
            sticky_config = self.sticky_messages[channel_id]
            
            # Lösche alte Sticky Message falls vorhanden
            old_message_id = self.last_sent_time.get(channel_id)
            if old_message_id:
                try:
                    old_message = await channel.fetch_message(int(old_message_id))
                    await old_message.delete()
                    logging.info(f"🗑️ Alte Sticky Message gelöscht: {old_message.id}")
                except (discord.NotFound, discord.Forbidden):
                    logging.info(f"⚠️ Alte Sticky Message bereits gelöscht oder nicht gefunden")
                except Exception as e:
                    logging.error(f"❌ Fehler beim Löschen der alten Nachricht: {e}")
            else:
                # Suche nach der letzten Sticky Message im Channel
                old_message = await self._find_last_sticky_message(channel)
                if old_message:
                    try:
                        await old_message.delete()
                        logging.info(f"🗑️ Alte Sticky Message gelöscht")
                    except Exception as e:
                        logging.error(f"❌ Fehler beim Löschen: {e}")
            
            # Erstelle neue Sticky Message
            embed = discord.Embed(
                title=sticky_config.get('title', 'Sticky Message'),
                description=sticky_config.get('message', ''),
                color=0x5865F2
            )
            
            # Zusätzliche Informationen
            if sticky_config.get('additional_info'):
                embed.add_field(
                    name="ℹ️ Zusätzliche Informationen",
                    value=sticky_config['additional_info'],
                    inline=False
                )
            
            # Footer
            if sticky_config.get('footer'):
                embed.set_footer(text=sticky_config['footer'])
            else:
                embed.set_footer(text="📌 Sticky Message")
            
            # Sende neue Sticky Message
            new_message = await channel.send(embed=embed)
            
            # Speichere neue Message ID
            self.last_sent_time[channel_id] = datetime.datetime.now()
            await self.save_sticky_messages()
            
            logging.info(f"✅ Neue Sticky Message gesendet")
            
        except asyncio.CancelledError:
            logging.info("⏹️ Sticky Message Aufgabe abgebrochen")
        except Exception as e:
            logging.error(f"❌ Fehler beim Senden der Sticky Message: {e}")

    async def _find_last_sticky_message(self, channel):
        """Findet die letzte Sticky Message im Channel"""
        try:
            async for message in channel.history(limit=50):
                if (message.author == self.bot.user and 
                    message.embeds and 
                    "Sticky Message" in str(message.embeds[0].footer.text)):
                    logging.info(f"🔍 Letzte Sticky Message gefunden: {message.id}")
                    return message
            
            logging.info(f"🔍 Keine passende Sticky Message gefunden")
            return None
            
        except Exception as e:
            logging.error(f"❌ Fehler beim Suchen der letzten Sticky Message: {e}")
            return None

    async def cleanup_server_data(self, guild_id):
        """Archiviert Sticky Message Daten für einen Server (24h Grace Period bei Bot-Kick)"""
        try:
            archived_count = 0
            channels_to_archive = []
            
            # Finde alle Channels des Servers in den Sticky Messages
            for channel_id in self.sticky_messages.keys():
                try:
                    # Versuche Channel zu finden um Guild ID zu ermitteln
                    channel = self.bot.get_channel(int(channel_id))
                    if channel and channel.guild.id == guild_id:
                        channels_to_archive.append(channel_id)
                        archived_count += 1
                except:
                    # Falls Channel nicht mehr existiert, archiviere trotzdem
                    # (kann bei Bot-Kick passieren)
                    pass
            
            if archived_count == 0:
                return 0
            
            # Archivierung vorbereiten
            import datetime
            archive_timestamp = datetime.datetime.now().isoformat()
            
            # Archivierte Sticky Messages laden/erstellen
            archived_messages = self.load_archived_sticky_messages()
            
            # Sticky Messages archivieren (nicht löschen!)
            for channel_id in channels_to_archive:
                if channel_id in self.sticky_messages:
                    # Zu Archiv hinzufügen mit Timestamp
                    archived_messages[channel_id] = {
                        **self.sticky_messages[channel_id],  # Alle originalen Daten kopieren
                        'archived_at': archive_timestamp,
                        'guild_id': guild_id,
                        'auto_delete_at': (datetime.datetime.now() + datetime.timedelta(hours=24)).isoformat()
                    }
                    
                    # Aus aktiven Sticky Messages entfernen
                    del self.sticky_messages[channel_id]
                
                # Lokale Caches bereinigen
                if channel_id in self.last_sent_time:
                    del self.last_sent_time[channel_id]
                if channel_id in self.last_message:
                    del self.last_message[channel_id]
                if channel_id in self.processing_channels:
                    self.processing_channels.remove(channel_id)
                if channel_id in self.sticky_tasks:
                    task = self.sticky_tasks[channel_id]
                    if not task.done():
                        task.cancel()
                    del self.sticky_tasks[channel_id]
            
            # Änderungen speichern
            self.save_sticky_messages()  # Aktive Messages
            self.save_archived_sticky_messages(archived_messages)  # Archivierte Messages
            
            logging.info(f"📦 {archived_count} Sticky Messages für Server {guild_id} archiviert (24h Grace Period)")
            logging.info(f"💡 Bot kann wieder eingeladen werden - Daten bleiben 24h erhalten!")
            
            return archived_count
            
        except Exception as e:
            logging.error(f"❌ Fehler beim Archivieren der Server-Daten: {e}")
            return 0

    def load_archived_sticky_messages(self):
        """Lädt archivierte Sticky Messages sicher verschlüsselt"""
        try:
            from src.utils.secure_storage import SecureStorage
            storage = SecureStorage(self.bot_token)
            return storage.load_encrypted_json("data/archived_sticky_messages.json")
        except Exception as e:
            logging.error(f"❌ Fehler beim sicheren Laden der archivierten Messages: {e}")
            # Fallback auf unverschlüsselte Datei (Migration)
            try:
                from src.utils.path_manager import get_application_path
                app_path = get_application_path()
                archive_file = os.path.join(app_path, 'data', 'archived_sticky_messages.json')
                
                if os.path.exists(archive_file):
                    with open(archive_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    logging.info("🔄 Migriere unverschlüsselte Archiv-Datei zu AES-256...")
                    # Sofort verschlüsselt speichern
                    self.save_archived_sticky_messages(data)
                    # Alte Datei löschen
                    os.remove(archive_file)
                    logging.info("✅ Archiv-Migration abgeschlossen")
                    return data
                
                return {}
            except Exception as fallback_error:
                logging.error(f"❌ Auch Fallback-Laden fehlgeschlagen: {fallback_error}")
                return {}

    def save_archived_sticky_messages(self, archived_messages):
        """Speichert archivierte Sticky Messages sicher verschlüsselt"""
        try:
            from src.utils.secure_storage import SecureStorage
            storage = SecureStorage(self.bot_token)
            success = storage.save_encrypted_json(archived_messages, "data/archived_sticky_messages.json")
            
            if success:
                logging.debug("🔐 Archivierte Sticky Messages sicher verschlüsselt gespeichert")
            else:
                raise Exception("Verschlüsseltes Speichern fehlgeschlagen")
                
        except Exception as e:
            logging.error(f"❌ Fehler beim sicheren Speichern der archivierten Messages: {e}")
            # Fallback auf unverschlüsselte Speicherung (nur im Notfall)
            try:
                from src.utils.path_manager import get_application_path
                app_path = get_application_path()
                data_dir = os.path.join(app_path, 'data')
                
                if not os.path.exists(data_dir):
                    os.makedirs(data_dir)
                    
                archive_file = os.path.join(data_dir, 'archived_sticky_messages.json')
                
                with open(archive_file, 'w', encoding='utf-8') as f:
                    json.dump(archived_messages, f, indent=2, ensure_ascii=False)
                    
                logging.warning("⚠️ Archivierte Messages unverschlüsselt gespeichert (Fallback)")
                
            except Exception as fallback_error:
                logging.error(f"❌ Auch Fallback-Speichern fehlgeschlagen: {fallback_error}")

    async def restore_archived_messages_for_guild(self, guild_id):
        """Stellt archivierte Sticky Messages für einen Server wieder her"""
        try:
            archived_messages = self.load_archived_sticky_messages()
            restored_count = 0
            channels_to_restore = []
            
            # Finde alle archivierten Messages für diese Guild
            for channel_id, data in archived_messages.items():
                if data.get('guild_id') == guild_id:
                    # Prüfe ob Channel noch existiert
                    channel = self.bot.get_channel(int(channel_id))
                    if channel:
                        channels_to_restore.append(channel_id)
            
            # Messages wiederherstellen
            for channel_id in channels_to_restore:
                archive_data = archived_messages[channel_id]
                
                # Archiv-spezifische Daten entfernen
                restored_data = {k: v for k, v in archive_data.items() 
                              if k not in ['archived_at', 'guild_id', 'auto_delete_at']}
                
                # Zu aktiven Messages hinzufügen
                self.sticky_messages[channel_id] = restored_data
                
                # Aus Archiv entfernen
                del archived_messages[channel_id]
                restored_count += 1
                
                logging.info(f"🔄 Sticky Message für Channel #{restored_data.get('channel_name', channel_id)} wiederhergestellt")
            
            if restored_count > 0:
                # Änderungen speichern
                self.save_sticky_messages()
                self.save_archived_sticky_messages(archived_messages)
                
                logging.info(f"✅ {restored_count} Sticky Messages für Server {guild_id} wiederhergestellt!")
            
            return restored_count
            
        except Exception as e:
            logging.error(f"❌ Fehler beim Wiederherstellen der Messages: {e}")
            return 0

    async def cleanup_expired_archives(self):
        """Löscht abgelaufene archivierte Messages (nach 24h)"""
        try:
            import datetime
            archived_messages = self.load_archived_sticky_messages()
            current_time = datetime.datetime.now()
            expired_channels = []
            
            for channel_id, data in archived_messages.items():
                try:
                    auto_delete_str = data.get('auto_delete_at')
                    if auto_delete_str:
                        auto_delete_time = datetime.datetime.fromisoformat(auto_delete_str)
                        if current_time >= auto_delete_time:
                            expired_channels.append(channel_id)
                except Exception as e:
                    logging.error(f"❌ Fehler beim Parsen des Löschdatums für Channel {channel_id}: {e}")
                    # Bei Parsing-Fehlern nach 48h löschen (sicher)
                    archived_str = data.get('archived_at')
                    if archived_str:
                        try:
                            archived_time = datetime.datetime.fromisoformat(archived_str)
                            if (current_time - archived_time).total_seconds() > (48 * 3600):  # 48h
                                expired_channels.append(channel_id)
                        except:
                            pass
            
            # Abgelaufene Archive löschen
            deleted_count = 0
            for channel_id in expired_channels:
                channel_name = archived_messages[channel_id].get('channel_name', 'Unbekannt')
                del archived_messages[channel_id]
                deleted_count += 1
                logging.info(f"🗑️ Abgelaufenes Archiv gelöscht: #{channel_name} (Channel {channel_id})")
            
            if deleted_count > 0:
                self.save_archived_sticky_messages(archived_messages)
                logging.info(f"🧹 {deleted_count} abgelaufene Archive bereinigt")
            
            return deleted_count
            
        except Exception as e:
            logging.error(f"❌ Fehler beim Bereinigen der Archive: {e}")
            return 0

async def setup(bot):
    await bot.add_cog(StickyCog(bot))