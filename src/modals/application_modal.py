import discord
from discord import ui, Interaction
from discord._types import ClientT

from src.components.application_service import ApplicationService


class ApplicationModal(ui.Modal, title='Bewerbung'):
    def __init__(self, application_service: ApplicationService, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.application_service = application_service

    vegan_label = 'Lebst du vegan? Wenn ja, seit wann und warum?'
    reason_label = 'Wie bist du auf uns aufmerksam geworden?'
    antifascist_label = 'Siehst du dich als Antifaschist*in und warum?'

    vegan = ui.TextInput(
        label=vegan_label,
        style=discord.TextStyle.paragraph,
        placeholder='Seit wann bist du vegan? Was sind deine Beweggründe?',
        required=True,
        max_length=1000
    )

    reason = ui.TextInput(
        label=reason_label,
        style=discord.TextStyle.paragraph,
        placeholder='Wie hast du von unserem Server erfahren? Hast du vielleicht schon andere vegane Communities besucht?',
        required=True,
        max_length=1000
    )

    antifascist = ui.TextInput(
        label=antifascist_label,
        style=discord.TextStyle.paragraph,
        placeholder='Wie stehst du zum Thema Antifaschismus? Siehst du dich selbst als Antifaschist*in und warum?',
        required=True,
        max_length=1000
    )

    async def on_submit(self, interaction: Interaction[ClientT], /) -> None:
        data = {
            self.vegan_label: self.vegan.value,
            self.reason_label: self.reason.value,
            self.antifascist_label: self.antifascist.value
        }

        message = await self.application_service.notify_team(
            guild=interaction.guild,
            user=interaction.user,
            data=data
        )

        await self.application_service.save_application(
            user_id=interaction.user.id,
            user_tag=str(interaction.user),
            data=data,
            team_message_id=message.id if message else None
        )

        await interaction.response.send_message(
            'Vielen Dank für deine Bewerbung! Das Team wird sie prüfen und sich bei dir melden.',
            ephemeral=True
        )
