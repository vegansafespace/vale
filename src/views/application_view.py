import discord

from main import container
from src.modals.application_modal import ApplicationModal
from src.helpers.env import NEW_USER_ROLE_ID

class ApplicationView(discord.ui.View):

    @discord.ui.button(
        label='Bewerben',
        style=discord.ButtonStyle.primary,
        custom_id='apply_button'
    )
    async def apply_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check if user has the NEW_USER_ROLE_ID
        if not any(role.id == NEW_USER_ROLE_ID for role in interaction.user.roles):
            await interaction.response.send_message(
                "Du hast nicht die erforderliche Berechtigung, um dich zu bewerben.",
                ephemeral=True
            )
            return

        application_service = container.application_service()

        if await application_service.has_application(interaction.user.id):
            await interaction.response.send_message(
                'Du hast bereits eine Bewerbung eingereicht. Bitte warte auf eine Antwort des Teams.',
                ephemeral=True
            )
            return

        await interaction.response.send_modal(ApplicationModal(application_service=application_service))
