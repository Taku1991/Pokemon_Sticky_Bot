import discord
from discord import ui
from src.utils.db_manager import save_json_file
from src.config.config import STICKY_FILE

class StickyModal(ui.Modal):
    def __init__(self, sticky_messages, title="Sticky Nachricht erstellen", 
                default_title="", default_message="", default_time=20, 
                default_example="", default_footer=""):  # Neue Parameter
        super().__init__(title=title)
        self.sticky_messages = sticky_messages
        
        self.title_input = ui.TextInput(
            label='Titel',
            placeholder='Gib hier den Titel ein...',
            required=True,
            max_length=256,
            default=default_title
        )
        self.message_input = ui.TextInput(
            label='Nachricht',
            placeholder='Gib hier deine Nachricht ein...',
            required=True,
            style=discord.TextStyle.paragraph,
            max_length=4000,
            default=default_message
        )
        self.example_input = ui.TextInput(
            label='Weitere Infos)',
            placeholder='Gib hier ein optionales Infos ein...',
            required=False,
            max_length=1000,
            default=default_example  # Hinzugefügt
        )
        self.footer_input = ui.TextInput(
            label='Footer Text (optional)',
            placeholder='z.B.: © 2025 Pokémon Hideout',
            required=False,
            max_length=1000,
            default=default_footer  # Hinzugefügt
        )
        self.time_input = ui.TextInput(
            label='Verzögerung (in Sekunden)',
            placeholder='Standard: 20',
            required=False,
            default=str(default_time)
        )
        
        self.add_item(self.title_input)
        self.add_item(self.message_input)
        self.add_item(self.example_input)
        self.add_item(self.footer_input)
        self.add_item(self.time_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            time = int(self.time_input.value or 20)
            if time < 5:
                await interaction.response.send_message(
                    "Die minimale Verzögerung beträgt 5 Sekunden.",
                    ephemeral=True
                )
                return
                
            channel_id = str(interaction.channel.id)
            channel_name = interaction.channel.name
            
            self.sticky_messages[channel_id] = {
                "title": self.title_input.value,
                "message": self.message_input.value,
                "delay": time,
                "channel_name": channel_name,
                "example": self.example_input.value if self.example_input.value else None,
                "footer": self.footer_input.value if self.footer_input.value else None
            }
            
            save_json_file(STICKY_FILE, self.sticky_messages)
            
            embed = discord.Embed(
                title=self.title_input.value,
                description=self.message_input.value,
                color=discord.Color.blue()
            )

            if self.example_input.value:
                embed.add_field(
                    name="Weitere Infos",
                    value=self.example_input.value,
                    inline=False
                )

            if self.footer_input.value:
                embed.set_footer(text=self.footer_input.value)

            await interaction.response.send_message(embed=embed)
            
        except ValueError:
            await interaction.response.send_message(
                "Bitte gib eine gültige Zahl für die Verzögerung ein.",
                ephemeral=True
            )