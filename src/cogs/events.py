import discord
from discord.ext import commands
import logging

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        """Wird ausgeführt wenn der Bot bereit ist"""
        logging.info(f'Bot ist bereit. Eingeloggt als {self.bot.user}')
        
        # 🔧 Optimierte Command-Synchronisation (Rate Limit vermeiden)
        try:
            logging.info("🔄 Synchronisiere Commands global...")
            
            # Nur GLOBAL synchronisieren (viel schneller, kein Rate Limit)
            synced = await self.bot.tree.sync()
            logging.info(f"✅ {len(synced)} Commands global synchronisiert")
            
            # Server-Count anzeigen
            server_count = len(self.bot.guilds)
            logging.info(f"🏠 Bot ist auf {server_count} Servern aktiv")
            
        except Exception as e:
            logging.error(f"❌ Fehler beim Synchronisieren der Commands: {e}")
            # Fallback - versuche es in 10 Sekunden nochmal
            import asyncio
            await asyncio.sleep(10)
            try:
                logging.info("🔄 Retry: Synchronisiere Commands...")
                synced = await self.bot.tree.sync()
                logging.info(f"✅ {len(synced)} Commands nach Retry synchronisiert")
            except Exception as retry_error:
                logging.error(f"❌ Auch Retry fehlgeschlagen: {retry_error}")
        
        # Sticky Messages beim Start laden
        try:
            sticky_cog = self.bot.get_cog('StickyCog')
            if sticky_cog:
                await sticky_cog.load_sticky_messages()
                logging.info("✅ Sticky Messages erfolgreich geladen")
                
                # 🆕 Cleanup abgelaufener Archive beim Bot-Start
                cleanup_count = await sticky_cog.cleanup_expired_archives()
                if cleanup_count > 0:
                    logging.info(f"🧹 {cleanup_count} abgelaufene Archive beim Start bereinigt")
                    
                # 🆕 Periodischen Cleanup-Task starten
                self.start_periodic_cleanup()
                
        except Exception as e:
            logging.error(f"❌ Fehler beim Laden der Sticky Messages: {e}")

    def start_periodic_cleanup(self):
        """Startet periodischen Cleanup-Task für abgelaufene Archive"""
        import asyncio
        
        async def periodic_cleanup():
            while True:
                try:
                    # Alle 6 Stunden prüfen
                    await asyncio.sleep(6 * 3600)  # 6 Stunden
                    
                    sticky_cog = self.bot.get_cog('StickyCog')
                    if sticky_cog:
                        cleanup_count = await sticky_cog.cleanup_expired_archives()
                        if cleanup_count > 0:
                            logging.info(f"🧹 Periodische Bereinigung: {cleanup_count} abgelaufene Archive gelöscht")
                        
                except Exception as e:
                    logging.error(f"❌ Fehler beim periodischen Cleanup: {e}")
        
        # Task im Hintergrund starten
        asyncio.create_task(periodic_cleanup())
        logging.info("🔄 Periodischer Archive-Cleanup gestartet (alle 6h)")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """Wird ausgeführt wenn der Bot einem neuen Server beitritt"""
        logging.info(f"🎉 Bot wurde zu Server '{guild.name}' hinzugefügt!")
        
        try:
            # 🔧 KEINE sofortige Server-spezifische Synchronisation mehr
            # Commands sind bereits global verfügbar
            logging.info(f"✅ Commands sind bereits global verfügbar für '{guild.name}'")
            
            # 🆕 Prüfe auf archivierte Sticky Messages für diesen Server
            sticky_cog = self.bot.get_cog('StickyCog')
            if sticky_cog:
                restored_count = await sticky_cog.restore_archived_messages_for_guild(guild.id)
                if restored_count > 0:
                    logging.info(f"🔄 {restored_count} Sticky Messages aus Archiv wiederhergestellt!")
                    
                    # Optional: Benachrichtigung an ersten verfügbaren Channel senden
                    try:
                        # Finde einen Text-Channel für die Benachrichtigung
                        for channel in guild.text_channels:
                            if channel.permissions_for(guild.me).send_messages:
                                import discord
                                embed = discord.Embed(
                                    title="🔄 Sticky Messages wiederhergestellt!",
                                    description=f"✅ **{restored_count} Sticky Messages** wurden automatisch aus dem 24h-Archiv wiederhergestellt!\n\n"
                                               f"📦 Grund: Bot war weniger als 24 Stunden weg\n"
                                               f"💡 Alle deine Sticky Messages sind wieder aktiv!",
                                    color=0x00ff00
                                )
                                embed.set_footer(text="💾 Daten werden automatisch 24h nach Bot-Kick gespeichert")
                                await channel.send(embed=embed)
                                break
                    except Exception as e:
                        logging.error(f"❌ Fehler beim Senden der Wiederherstellungs-Benachrichtigung: {e}")
            
        except Exception as e:
            logging.error(f"❌ Fehler beim Guild-Join für Server {guild.name}: {e}")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        """Wird ausgeführt wenn der Bot einen Server verlässt oder gekickt wird"""
        logging.info(f"👋 Bot wurde von Server '{guild.name}' (ID: {guild.id}) entfernt")
        
        try:
            # 1. Bot-Berechtigungen für diesen Server löschen
            from src.utils.permissions import load_permissions, save_permissions
            permissions = load_permissions()
            guild_str = str(guild.id)
            
            if guild_str in permissions:
                # Anzahl der betroffenen User loggen
                masters_count = len(permissions[guild_str].get('masters', []))
                editors_count = len(permissions[guild_str].get('editors', []))
                
                # Server aus Berechtigungen entfernen
                del permissions[guild_str]
                save_permissions(permissions)
                
                logging.info(f"🧹 Berechtigungen für Server '{guild.name}' bereinigt: "
                           f"{masters_count} Masters, {editors_count} Editors entfernt")
            
            # 2. Sticky Messages für diesen Server löschen
            sticky_cog = self.bot.get_cog('Sticky')
            if sticky_cog:
                removed_count = await sticky_cog.cleanup_server_data(guild.id)
                if removed_count > 0:
                    logging.info(f"🧹 {removed_count} Sticky Messages für Server '{guild.name}' entfernt")
            
            logging.info(f"✅ Vollständige Bereinigung für Server '{guild.name}' abgeschlossen")
            
        except Exception as e:
            logging.error(f"❌ Fehler beim Bereinigen der Server-Daten für '{guild.name}': {e}")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Wird ausgeführt wenn ein Member einen Server verlässt"""
        # Nur Bot Master/Editor bereinigen, nicht bei normalem Member-Leave
        try:
            from src.utils.permissions import is_bot_admin, is_bot_editor, remove_bot_permissions
            
            # Prüfen ob der verlassende User Bot-Berechtigungen hatte
            if is_bot_admin(member.id, member.guild.id) or is_bot_editor(member.id, member.guild.id):
                # Berechtigungen entfernen
                success = remove_bot_permissions(member.id, member.guild.id)
                
                if success:
                    logging.info(f"🧹 Bot-Berechtigungen für verlassenden User '{member.display_name}' "
                               f"auf Server '{member.guild.name}' entfernt")
                    
                    # Warnung wenn alle Masters weg sind
                    from src.utils.permissions import load_permissions
                    permissions = load_permissions()
                    guild_str = str(member.guild.id)
                    
                    if guild_str in permissions:
                        remaining_masters = permissions[guild_str].get('masters', [])
                        if not remaining_masters:
                            logging.warning(f"⚠️ Server '{member.guild.name}' hat keine Bot Masters mehr! "
                                          f"Jemand muss '/setup_botmaster' verwenden.")
                
        except Exception as e:
            logging.error(f"❌ Fehler beim Bereinigen von Member-Berechtigungen: {e}")

    @commands.Cog.listener()
    async def on_message(self, message):
        """Wird bei jeder neuen Nachricht ausgeführt"""
        # Ignoriere Bot-Nachrichten
        if message.author.bot:
            return
        
        # Sticky Message Handler
        try:
            sticky_cog = self.bot.get_cog('Sticky')
            if sticky_cog:
                await sticky_cog.handle_message_for_sticky(message)
        except Exception as e:
            logging.error(f"❌ Fehler beim Sticky Message Handling: {e}")

async def setup(bot):
    await bot.add_cog(Events(bot))