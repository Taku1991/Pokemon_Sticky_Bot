import discord
from discord import app_commands
from discord.ext import commands
import logging

class HelpView(discord.ui.View):
    """Interactive Help View mit Buttons für verschiedene Kategorien"""
    
    def __init__(self):
        super().__init__(timeout=300)  # 5 Minuten Timeout
    
    @discord.ui.button(label="🔐 Admin Commands", style=discord.ButtonStyle.primary)
    async def admin_help(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🔐 Administrator Commands",
            description="Befehle für Bot-Master und Server-Verwaltung",
            color=0x5865F2
        )
        
        embed.add_field(
            name="/setup_botmaster",
            value="• Macht dich zum ersten Bot-Master auf dem Server\n• Nur einmal pro Server möglich\n• Danach können weitere Master hinzugefügt werden",
            inline=False
        )
        
        embed.add_field(
            name="/add_editor @benutzer",
            value="• Gibt einem Benutzer Bot-Editor Rechte\n• Nur Bot-Master können das\n• Editoren können Sticky Messages verwalten",
            inline=False
        )
        
        embed.add_field(
            name="/remove_editor @benutzer",
            value="• Entfernt Bot-Editor Rechte\n• Nur Bot-Master können das",
            inline=False
        )
        
        embed.add_field(
            name="/list_roles",
            value="• Zeigt alle Bot-Master und Editoren des Servers\n• Für alle sichtbar",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="📌 Sticky Commands", style=discord.ButtonStyle.success)
    async def sticky_help(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="📌 Sticky Message Commands",
            description="Befehle für persistente Nachrichten (Bot-Master + Editoren)",
            color=0x57F287
        )
        
        embed.add_field(
            name="/set_sticky",
            value="• Erstellt eine neue Sticky Message für den aktuellen Channel\n• Öffnet ein Formular zum Ausfüllen\n• Mindestens 5 Sekunden Verzögerung",
            inline=False
        )
        
        embed.add_field(
            name="/edit_sticky",
            value="• Bearbeitet die Sticky Message des aktuellen Channels\n• Öffnet Formular mit aktuellen Werten\n• Falls keine Sticky vorhanden: Fehlermeldung",
            inline=False
        )
        
        embed.add_field(
            name="/remove_sticky",
            value="• Löscht die Sticky Message aus dem aktuellen Channel\n• Permanent - kann nicht rückgängig gemacht werden",
            inline=False
        )
        
        embed.add_field(
            name="/sticky_list",
            value="• Zeigt alle aktiven Sticky Messages auf dem Server\n• Mit Channel-Namen und Einstellungen",
            inline=False
        )
        
        embed.add_field(
            name="/update_sticky_time [sekunden]",
            value="• Ändert nur die Verzögerung einer bestehenden Sticky\n• Minimum: 5 Sekunden\n• Wirkt sofort",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="💡 Tipps & Tricks", style=discord.ButtonStyle.secondary)
    async def tips_help(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="💡 Tipps & Tricks für StickyBot",
            description="Nützliche Hinweise für die optimale Nutzung",
            color=0xFAA61A
        )
        
        embed.add_field(
            name="🎯 Sticky Messages Funktionsweise",
            value="• Erscheinen automatisch nach jeder normalen Nachricht\n• Löschen automatisch die vorherige Sticky\n• Immer am Ende des Channels sichtbar\n• Enthalten zufällige Pokémon-Bilder",
            inline=False
        )
        
        embed.add_field(
            name="⚡ Performance-Tipps",
            value="• Nicht zu kurze Verzögerungen verwenden (min. 10-15s empfohlen)\n• Maximal 2-3 Sticky Messages pro Server\n• Kurze, prägnante Nachrichten sind besser",
            inline=False
        )
        
        embed.add_field(
            name="🔧 Troubleshooting",
            value="• Sticky erscheint nicht? Prüfe Berechtigungen des Bots\n• Commands funktionieren nicht? `/list_roles` überprüfen\n• Bot reagiert nicht? Administrator kontaktieren",
            inline=False
        )
        
        embed.add_field(
            name="🎨 Message-Formatting",
            value="• **Fett**, *Kursiv*, ~~Durchgestrichen~~\n• Links werden automatisch erkannt\n• Emojis funktionieren normal",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="📋 Zeigt alle verfügbaren Befehle")
    async def help_command(self, interaction: discord.Interaction):
        """Zeigt alle verfügbaren Befehle mit interaktivem Interface"""
        try:
            embed = discord.Embed(
                title="📋 StickyBot - Hilfe & Befehle",
                description=f"Willkommen zum StickyBot Help Center! 🎉\n\n"
                           f"**Server:** {interaction.guild.name}\n"
                           f"**Deine Rolle:** {'Bot-Master' if self.is_bot_admin(interaction.user.id, interaction.guild.id) else 'Bot-Editor' if self.is_bot_editor(interaction.user.id, interaction.guild.id) else 'Normal'}\n\n"
                           f"📌 **Was ist StickyBot?**\n"
                           f"StickyBot erstellt persistente Nachrichten, die nach jeder normalen Nachricht automatisch erneut gesendet werden. Perfect für Regeln, Ankündigungen oder wichtige Informationen!",
                color=0x5865F2
            )
            
            # Admin Commands
            admin_commands = [
                "`/setup_botmaster` - Erstmalige Bot-Master Registrierung",
                "`/add_editor @user` - Editor-Rechte vergeben",
                "`/remove_editor @user` - Editor-Rechte entziehen", 
                "`/list_roles` - Alle Berechtigungen anzeigen"
            ]
            
            embed.add_field(
                name="🔐 Admin Commands (Nur Bot-Master)",
                value="\n".join(admin_commands),
                inline=False
            )
            
            # Sticky Commands
            sticky_commands = [
                "`/set_sticky` - Neue Sticky Message erstellen",
                "`/edit_sticky` - Sticky des Channels bearbeiten",
                "`/remove_sticky` - Sticky des Channels löschen",
                "`/sticky_list` - Alle Sticky Messages anzeigen",
                "`/update_sticky_time [sek]` - Verzögerung ändern"
            ]
            
            embed.add_field(
                name="📌 Sticky Message Commands (Botmaster + Editoren)",
                value="\n".join(sticky_commands),
                inline=False
            )
            
            embed.add_field(
                name="ℹ️ Wichtige Hinweise",
                value="• Benutze `/setup_botmaster` um Bot-Master zu werden\n"
                      "• Bot-Master können Editoren verwalten\n"
                      "• Jeder Server hat eigene Berechtigungen\n"
                      "• Mindestens 5 Sekunden Verzögerung für Sticky Messages",
                inline=False
            )
            
            embed.set_footer(text="💡 Klicke auf die Buttons für detaillierte Hilfe zu einzelnen Kategorien")
            
            # Buttons für detaillierte Hilfe
            view = HelpView()
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            logging.error(f"Fehler beim Anzeigen der Hilfe: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ Ein Fehler ist beim Laden der Hilfe aufgetreten.", 
                    ephemeral=True
                )
    
    def is_bot_admin(self, user_id, guild_id):
        """Prüft ob User Bot Admin ist"""
        try:
            from src.utils.permissions import is_bot_admin
            return is_bot_admin(user_id, guild_id)
        except:
            return False
    
    def is_bot_editor(self, user_id, guild_id):
        """Prüft ob User Bot Editor ist"""
        try:
            from src.utils.permissions import is_bot_editor
            return is_bot_editor(user_id, guild_id)
        except:
            return False

async def setup(bot):
    await bot.add_cog(HelpCog(bot))