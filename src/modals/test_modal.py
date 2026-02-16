import discord
from discord import ui, Interaction
from discord._types import ClientT


class TestModal(ui.Modal, title='Test'):
    name = ui.TextInput(label='Name')
    answer = ui.TextInput(label='Answer', style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: Interaction[ClientT], /) -> None:
        await interaction.response.send_message(f'Thank you for your submission, {self.name}!')
