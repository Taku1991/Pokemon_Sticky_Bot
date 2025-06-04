import discord
from discord import app_commands
from discord.ext import commands
from src.utils.permissions import is_bot_admin, add_bot_master, add_bot_editor, load_permissions, save_permissions, save_permissions_from_bot_roles
from src.utils.path_manager import get_application_path
import os
import json
import logging

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def load_bot_roles(self):
        """Lädt die Bot-Rollen aus dem einheitlichen verschlüsselten System"""
        try:
            # Verwende das einheitliche Permission-System
            permissions = load_permissions()
            
            # Konvertiere zu bot_roles Format
            bot_roles = {}
            for guild_id, perms in permissions.items():
                bot_roles[guild_id] = {
                    'admin': perms.get('masters', []),
                    'editor': perms.get('editors', []),
                    'viewer': []
                }
            
            logging.debug(f"🔐 Bot-Rollen geladen: {len(bot_roles)} Server")
            return bot_roles
            
        except Exception as e:
            logging.error(f"❌ Fehler beim Laden der Bot-Rollen: {e}")
            return {}

    def save_bot_roles(self, bot_roles):
        """Speichert die Bot-Rollen über das einheitliche verschlüsselte System"""
        try:
            # Verwende das einheitliche Permission-System
            success = save_permissions_from_bot_roles(bot_roles)
            
            if success:
                logging.info(f"🔐 Bot-Rollen sicher gespeichert: {len(bot_roles)} Server")
                return True
            else:
                logging.error("❌ Fehler beim Speichern der Bot-Rollen")
                return False
                
        except Exception as e:
            logging.error(f"❌ Fehler beim Speichern der Bot-Rollen: {e}")
            return False

    @app_commands.command(name="setup_botmaster", description="Macht dich zum Bot Master (einmalig pro Server)")
    async def setup_botmaster(self, interaction: discord.Interaction):
        """Setup Bot Master - nur einmal pro Server möglich"""
        try:
            # 🚀 SOFORT antworten um 3s Timeout zu vermeiden
            await interaction.response.defer(ephemeral=True)
            
            bot_roles = self.load_bot_roles()
            guild_str = str(interaction.guild.id)
            user_str = str(interaction.user.id)
            
            # Prüfe ob bereits ein Admin auf diesem Server existiert
            if guild_str in bot_roles:
                existing_admins = bot_roles[guild_str].get('admin', [])
                if existing_admins:
                    # Prüfe ob die bestehenden Admins noch auf dem Server sind
                    active_admins = []
                    for admin_id in existing_admins:
                        try:
                            member = interaction.guild.get_member(int(admin_id))
                            if member:
                                active_admins.append(admin_id)
                        except:
                            pass  # User nicht mehr auf Server
                    
                    if active_admins:
                        # Es gibt noch aktive Bot Masters
                        await interaction.followup.send(
                            f"❌ Es gibt bereits Bot Master auf diesem Server!\n"
                            f"Aktuelle Masters: {len(active_admins)} User\n\n"
                            f"Verwende `/list_roles` um alle zu sehen.",
                            ephemeral=True
                        )
                        return
                    else:
                        # Alle alten Masters haben den Server verlassen - bereinigen
                        logging.info(f"🧹 Verwaiste Bot Masters auf Server {interaction.guild.name} erkannt - bereinige...")
                        bot_roles[guild_str]['admin'] = []
                        bot_roles[guild_str]['editor'] = []  # Auch Editors bereinigen
            
            # Erstelle neue Admin-Struktur
            if guild_str not in bot_roles:
                bot_roles[guild_str] = {
                    'admin': [],
                    'editor': [],
                    'viewer': []
                }
            
            # User als ersten Admin hinzufügen
            bot_roles[guild_str]['admin'] = [user_str]
            
            # Speichern
            if self.save_bot_roles(bot_roles):
                await interaction.followup.send(
                    f"🎉 **Setup erfolgreich!**\n\n"
                    f"👑 {interaction.user.mention} ist jetzt **Bot Master** auf diesem Server!\n\n"
                    f"**Du kannst jetzt:**\n"
                    f"• `/add_editor @user` - Editoren hinzufügen\n"
                    f"• `/remove_editor @user` - Editoren entfernen\n"
                    f"• `/list_roles` - Alle Rollen anzeigen\n"
                    f"• `/set_sticky` - Sticky Messages erstellen\n\n"
                    f"🔧 **Verwende das Kontrollzentrum für erweiterte Verwaltung!**",
                    ephemeral=True
                )
                logging.info(f"✅ Neuer Bot Master: {interaction.user.name} auf Server {interaction.guild.name}")
            else:
                await interaction.followup.send(
                    "❌ Fehler beim Speichern der Konfiguration!",
                    ephemeral=True
                )
            
        except Exception as e:
            logging.error(f"❌ setup_botmaster Fehler: {e}")
            try:
                # Prüfe ob Response schon gesendet wurde
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        f"❌ Ein Fehler ist aufgetreten: {str(e)}",
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        f"❌ Ein Fehler ist aufgetreten: {str(e)}",
                        ephemeral=True
                    )
            except Exception as followup_error:
                logging.error(f"❌ Auch Fehler-Response fehlgeschlagen: {followup_error}")

    @app_commands.command(name="add_editor", description="Fügt einen Bot Editor hinzu (nur Bot Master)")
    async def add_editor(self, interaction: discord.Interaction, benutzer: discord.Member):
        """Fügt einen Bot Editor hinzu"""
        try:
            # 🚀 Sofort antworten
            await interaction.response.defer(ephemeral=True)
            
            # Berechtigungsprüfung
            if not is_bot_admin(interaction.user.id, interaction.guild.id):
                await interaction.followup.send(
                    "❌ Nur Bot Master können Editoren hinzufügen!",
                    ephemeral=True
                )
                return
            
            # Prüfe ob User bereits Admin ist
            if is_bot_admin(benutzer.id, interaction.guild.id):
                await interaction.followup.send(
                    f"❌ {benutzer.mention} ist bereits Bot Master!",
                    ephemeral=True
                )
                return
            
            # Editor hinzufügen
            if add_bot_editor(benutzer.id, interaction.guild.id):
                await interaction.followup.send(
                    f"✅ **Editor hinzugefügt!**\n\n"
                    f"✏️ {benutzer.mention} ist jetzt **Bot Editor** und kann:\n"
                    f"• `/set_sticky` - Sticky Messages erstellen\n"
                    f"• `/edit_sticky` - Sticky Messages bearbeiten\n"
                    f"• `/remove_sticky` - Sticky Messages löschen\n"
                    f"• `/sticky_list` - Alle Sticky Messages anzeigen",
                    ephemeral=True
                )
                logging.info(f"✅ Neuer Editor: {benutzer.name} auf Server {interaction.guild.name}")
            else:
                await interaction.followup.send(
                    "❌ Fehler beim Hinzufügen des Editors!",
                    ephemeral=True
                )
            
        except Exception as e:
            logging.error(f"❌ add_editor Fehler: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(f"❌ Ein Fehler ist aufgetreten: {str(e)}", ephemeral=True)
                else:
                    await interaction.followup.send(f"❌ Ein Fehler ist aufgetreten: {str(e)}", ephemeral=True)
            except:
                pass

    @app_commands.command(name="remove_editor", description="Entfernt einen Bot Editor (nur Bot Master)")
    async def remove_editor(self, interaction: discord.Interaction, benutzer: discord.Member):
        """Entfernt einen Bot Editor"""
        try:
            # 🚀 Sofort antworten
            await interaction.response.defer(ephemeral=True)
            
            # Berechtigungsprüfung
            if not is_bot_admin(interaction.user.id, interaction.guild.id):
                await interaction.followup.send(
                    "❌ Nur Bot Master können Editoren entfernen!",
                    ephemeral=True
                )
                return
            
            bot_roles = self.load_bot_roles()
            guild_str = str(interaction.guild.id)
            user_str = str(benutzer.id)
            
            if guild_str not in bot_roles:
                await interaction.followup.send(
                    "❌ Keine Bot-Konfiguration für diesen Server gefunden!",
                    ephemeral=True
                )
                return
            
            # Prüfe ob User Editor ist
            editors = bot_roles[guild_str].get('editor', [])
            if user_str not in editors:
                await interaction.followup.send(
                    f"❌ {benutzer.mention} ist kein Bot Editor!",
                    ephemeral=True
                )
                return
            
            # Editor entfernen
            bot_roles[guild_str]['editor'].remove(user_str)
            
            if self.save_bot_roles(bot_roles):
                await interaction.followup.send(
                    f"✅ **Editor entfernt!**\n\n"
                    f"{benutzer.mention} ist kein Bot Editor mehr.",
                    ephemeral=True
                )
                logging.info(f"✅ Editor entfernt: {benutzer.name} von Server {interaction.guild.name}")
            else:
                await interaction.followup.send(
                    "❌ Fehler beim Speichern der Konfiguration!",
                    ephemeral=True
                )
            
        except Exception as e:
            logging.error(f"❌ remove_editor Fehler: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(f"❌ Ein Fehler ist aufgetreten: {str(e)}", ephemeral=True)
                else:
                    await interaction.followup.send(f"❌ Ein Fehler ist aufgetreten: {str(e)}", ephemeral=True)
            except:
                pass

    @app_commands.command(name="list_roles", description="Zeigt alle Bot-Rollen auf diesem Server")
    async def list_roles(self, interaction: discord.Interaction):
        """Zeigt alle Bot-Rollen an"""
        try:
            # 🚀 Sofort antworten
            await interaction.response.defer(ephemeral=True)
            
            bot_roles = self.load_bot_roles()
            guild_str = str(interaction.guild.id)
            
            if guild_str not in bot_roles:
                await interaction.followup.send(
                    "❌ Keine Bot-Rollen auf diesem Server konfiguriert!\n\n"
                    "Verwende `/setup_botmaster` um zu beginnen.",
                    ephemeral=True
                )
                return
            
            embed = discord.Embed(
                title="🎭 Bot-Rollen Übersicht",
                description=f"Berechtigungen auf **{interaction.guild.name}**",
                color=0x5865F2
            )
            
            # Bot Masters
            admins = bot_roles[guild_str].get('admin', [])
            if admins:
                admin_mentions = []
                for admin_id in admins:
                    try:
                        admin_user = interaction.guild.get_member(int(admin_id))
                        admin_mentions.append(admin_user.mention if admin_user else f"User ID: {admin_id}")
                    except:
                        admin_mentions.append(f"User ID: {admin_id}")
                
                embed.add_field(
                    name="👑 Bot Masters",
                    value="\n".join(admin_mentions) + "\n\n**Können alles verwalten**",
                    inline=False
                )
            else:
                embed.add_field(
                    name="👑 Bot Masters", 
                    value="Keine Bot Masters konfiguriert", 
                    inline=False
                )
            
            # Bot Editors
            editors = bot_roles[guild_str].get('editor', [])
            if editors:
                editor_mentions = []
                for editor_id in editors:
                    try:
                        editor_user = interaction.guild.get_member(int(editor_id))
                        editor_mentions.append(editor_user.mention if editor_user else f"User ID: {editor_id}")
                    except:
                        editor_mentions.append(f"User ID: {editor_id}")
                
                embed.add_field(
                    name="✏️ Bot Editors",
                    value="\n".join(editor_mentions) + "\n\n**Können Sticky Messages verwalten**",
                    inline=False
                )
            else:
                embed.add_field(
                    name="✏️ Bot Editors", 
                    value="Keine Bot Editors konfiguriert", 
                    inline=False
                )
            
            embed.set_footer(text="💡 Bot Masters können Editoren hinzufügen/entfernen")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logging.error(f"❌ list_roles Fehler: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(f"❌ Ein Fehler ist aufgetreten: {str(e)}", ephemeral=True)
                else:
                    await interaction.followup.send(f"❌ Ein Fehler ist aufgetreten: {str(e)}", ephemeral=True)
            except:
                pass

    @app_commands.command(name="transfer_master", description="Überträgt Bot Master Rolle an anderen User")
    async def transfer_master(self, interaction: discord.Interaction, neuer_master: discord.Member):
        """Überträgt Bot Master Rolle"""
        try:
            # 🚀 Sofort antworten
            await interaction.response.defer(ephemeral=True)
            
            # Berechtigungsprüfung
            if not is_bot_admin(interaction.user.id, interaction.guild.id):
                await interaction.followup.send(
                    "❌ Nur Bot Master können ihre Rolle übertragen!",
                    ephemeral=True
                )
                return
            
            bot_roles = self.load_bot_roles()
            guild_str = str(interaction.guild.id)
            new_master_str = str(neuer_master.id)
            current_user_str = str(interaction.user.id)
            
            if guild_str not in bot_roles:
                await interaction.followup.send(
                    "❌ Keine Bot-Konfiguration gefunden!",
                    ephemeral=True
                )
                return
            
            # Neuen Master zu Admin-Liste hinzufügen
            admins = bot_roles[guild_str].get('admin', [])
            if new_master_str not in admins:
                admins.append(new_master_str)
            
            # Aus Editor-Liste entfernen falls vorhanden
            editors = bot_roles[guild_str].get('editor', [])
            if new_master_str in editors:
                editors.remove(new_master_str)
            
            bot_roles[guild_str]['admin'] = admins
            bot_roles[guild_str]['editor'] = editors
            
            if self.save_bot_roles(bot_roles):
                await interaction.followup.send(
                    f"✅ **Master-Rolle übertragen!**\n\n"
                    f"👑 {neuer_master.mention} ist jetzt ebenfalls **Bot Master**!\n\n"
                    f"**Beide Master können jetzt:**\n"
                    f"• Editoren verwalten\n"
                    f"• Sticky Messages erstellen\n"
                    f"• Alle Bot-Funktionen nutzen",
                    ephemeral=True
                )
                logging.info(f"✅ Master-Rolle übertragen: {neuer_master.name} auf Server {interaction.guild.name}")
            else:
                await interaction.followup.send(
                    "❌ Fehler beim Speichern der Konfiguration!",
                    ephemeral=True
                )
            
        except Exception as e:
            logging.error(f"❌ transfer_master Fehler: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(f"❌ Ein Fehler ist aufgetreten: {str(e)}", ephemeral=True)
                else:
                    await interaction.followup.send(f"❌ Ein Fehler ist aufgetreten: {str(e)}", ephemeral=True)
            except:
                pass

    @app_commands.command(name="restore_sticky_archive", description="Zeigt archivierte Sticky Messages an und kann sie wiederherstellen")
    async def restore_sticky_archive(self, interaction: discord.Interaction):
        """Zeigt archivierte Sticky Messages für diesen Server an"""
        try:
            # 🚀 Sofort antworten
            await interaction.response.defer(ephemeral=True)
            
            # Berechtigungsprüfung
            if not is_bot_admin(interaction.user.id, interaction.guild.id):
                await interaction.followup.send(
                    "❌ Nur Bot Master können Archive verwalten!",
                    ephemeral=True
                )
                return
            
            # Sticky Cog holen
            sticky_cog = self.bot.get_cog('StickyCog')
            if not sticky_cog:
                await interaction.followup.send(
                    "❌ Sticky System nicht verfügbar!",
                    ephemeral=True
                )
                return
            
            # Archivierte Messages für diesen Server laden
            archived_messages = sticky_cog.load_archived_sticky_messages()
            server_archives = {}
            
            for channel_id, data in archived_messages.items():
                if data.get('guild_id') == interaction.guild.id:
                    server_archives[channel_id] = data
            
            if not server_archives:
                await interaction.followup.send(
                    "📭 **Keine archivierten Sticky Messages gefunden**\n\n"
                    "Entweder wurden keine Messages archiviert oder\n"
                    "die 24h Grace Period ist bereits abgelaufen.",
                    ephemeral=True
                )
                return
            
            # Embed mit archivierten Messages erstellen
            import discord
            import datetime
            
            embed = discord.Embed(
                title="📦 Archivierte Sticky Messages",
                description=f"**Server:** {interaction.guild.name}\n"
                           f"**Anzahl:** {len(server_archives)} archivierte Messages\n\n"
                           "💡 Verwende `/restore_sticky_archive` erneut um wiederherzustellen!",
                color=0xffa500
            )
            
            for channel_id, data in server_archives.items():
                channel_name = data.get('channel_name', 'Unbekannter Channel')
                title = data.get('title', 'Unbenannt')
                
                # Archivierungs-Zeit formatieren
                try:
                    archived_str = data.get('archived_at', '')
                    if archived_str:
                        archived_time = datetime.datetime.fromisoformat(archived_str)
                        archived_formatted = archived_time.strftime('%d.%m.%Y %H:%M')
                    else:
                        archived_formatted = 'Unbekannt'
                        
                    # Löschzeit berechnen
                    auto_delete_str = data.get('auto_delete_at', '')
                    if auto_delete_str:
                        auto_delete_time = datetime.datetime.fromisoformat(auto_delete_str)
                        remaining = auto_delete_time - datetime.datetime.now()
                        if remaining.total_seconds() > 0:
                            hours_left = int(remaining.total_seconds() / 3600)
                            remaining_text = f"{hours_left}h verbleibend"
                        else:
                            remaining_text = "⚠️ Abgelaufen"
                    else:
                        remaining_text = 'Unbekannt'
                        
                except Exception:
                    archived_formatted = 'Fehler beim Formatieren'
                    remaining_text = 'Unbekannt'
                
                embed.add_field(
                    name=f"#{channel_name}",
                    value=f"**Titel:** {title}\n"
                          f"**Archiviert:** {archived_formatted}\n"
                          f"**Läuft ab:** {remaining_text}",
                    inline=True
                )
            
            embed.set_footer(text="🔄 Drücke den Button um ALLE archivierten Messages wiederherzustellen")
            
            # Button zum Wiederherstellen hinzufügen
            view = RestoreArchiveView(sticky_cog, interaction.guild.id)
            
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            logging.error(f"❌ restore_sticky_archive Fehler: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(f"❌ Ein Fehler ist aufgetreten: {str(e)}", ephemeral=True)
                else:
                    await interaction.followup.send(f"❌ Ein Fehler ist aufgetreten: {str(e)}", ephemeral=True)
            except:
                pass

    @app_commands.command(name="debug_permissions", description="🔍 Debug: Zeigt alle Berechtigungen (Bot Master only)")
    async def debug_permissions(self, interaction: discord.Interaction):
        """Debug-Command für Berechtigungen"""
        try:
            await interaction.response.defer(ephemeral=True)
            
            if not is_bot_admin(interaction.user.id, interaction.guild.id):
                await interaction.followup.send(
                    "❌ Nur Bot Master können Debug-Informationen abrufen!",
                    ephemeral=True
                )
                return
            
            # Debug-Informationen sammeln
            from src.utils.permissions import load_permissions
            
            permissions = load_permissions()
            
            if not permissions:
                await interaction.followup.send("📭 Keine Berechtigungen konfiguriert.", ephemeral=True)
                return
            
            # Format für Discord
            debug_text = "🔍 **Berechtigungen Debug**\n\n"
            
            for guild_id, perms in permissions.items():
                masters = perms.get('masters', [])
                editors = perms.get('editors', [])
                
                # Guild-Name versuchen zu ermitteln
                guild_name = "Unbekannt"
                try:
                    guild = self.bot.get_guild(int(guild_id))
                    if guild:
                        guild_name = guild.name
                except:
                    pass
                
                debug_text += f"🏠 **{guild_name}** (`{guild_id}`)\n"
                debug_text += f"   👑 Masters: {len(masters)}\n"
                debug_text += f"   ✏️ Editors: {len(editors)}\n\n"
            
            await interaction.followup.send(debug_text, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Debug-Fehler: {str(e)}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AdminCog(bot))


class RestoreArchiveView(discord.ui.View):
    """View mit Button zum Wiederherstellen archivierter Sticky Messages"""
    
    def __init__(self, sticky_cog, guild_id):
        super().__init__(timeout=300)  # 5 Minuten Timeout
        self.sticky_cog = sticky_cog
        self.guild_id = guild_id
    
    @discord.ui.button(label="🔄 Alle wiederherstellen", style=discord.ButtonStyle.success)
    async def restore_all_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            # Nochmal Berechtigung prüfen
            if not is_bot_admin(interaction.user.id, interaction.guild.id):
                await interaction.response.send_message(
                    "❌ Nur Bot Master können Archive wiederherstellen!",
                    ephemeral=True
                )
                return
            
            # Wiederherstellen
            restored_count = await self.sticky_cog.restore_archived_messages_for_guild(self.guild_id)
            
            if restored_count > 0:
                embed = discord.Embed(
                    title="✅ Wiederherstellung erfolgreich!",
                    description=f"**{restored_count} Sticky Messages** wurden erfolgreich wiederhergestellt!\n\n"
                               f"🎉 Alle archivierten Messages sind wieder aktiv\n"
                               f"📝 Sie funktionieren wie vor dem Bot-Kick",
                    color=0x00ff00
                )
                embed.set_footer(text="💡 Die Messages wurden aus dem Archiv entfernt")
                
                # Button deaktivieren
                button.disabled = True
                button.label = "✅ Wiederhergestellt"
                
                await interaction.response.edit_message(embed=embed, view=self)
            else:
                await interaction.response.send_message(
                    "❌ Keine Messages zum Wiederherstellen gefunden oder Fehler aufgetreten!",
                    ephemeral=True
                )
                
        except Exception as e:
            logging.error(f"❌ Fehler beim Wiederherstellen über Button: {e}")
            await interaction.response.send_message(
                f"❌ Fehler beim Wiederherstellen: {str(e)}",
                ephemeral=True
            )
    
    @discord.ui.button(label="❌ Abbrechen", style=discord.ButtonStyle.secondary)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="❌ Wiederherstellung abgebrochen",
            description="Die archivierten Messages bleiben im Archiv\n"
                       "bis sie automatisch nach 24h gelöscht werden.",
            color=0x808080
        )
        
        # Buttons deaktivieren
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)
