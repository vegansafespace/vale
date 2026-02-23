from logging import Logger
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from dependency_injector.wiring import Provide, inject

from src.helpers.env import NEW_USER_ROLE_ID, VEGAN_ROLE_ID, REPORTS_CHANNEL_ID, TEAM_APPLICATIONS_CHANNEL_ID
from src.helpers.config_keys import ConfigKey
from src.main import container
from src.modals.application_modal import ApplicationModal
from src.modals.test_modal import TestModal
from src.components.application_service import ApplicationService
from src.vale import Vale


class UserUtils(commands.Cog):
    @inject
    def __init__(
            self,
            logger: Logger,
            bot: Vale,
            application_service: ApplicationService,
            configuration_service: Provide["configuration_service"]
    ):
        self.logger = logger
        self.bot = bot
        self.application_service = application_service
        self.configuration_service = configuration_service

        self.bot.tree.add_command(
            app_commands.ContextMenu(
                name='Beitrittsdatum zeigen',
                callback=self.show_join_date,
            )
        )

        self.bot.tree.add_command(
            app_commands.ContextMenu(
                name='Dem Team melden',
                callback=self.report_message,
            )
        )

    @app_commands.checks.has_role(VEGAN_ROLE_ID)
    async def show_join_date(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.send_message(
            f'{member} ist <t:{member.joined_at.timestamp()}:R> gejoined',
            ephemeral=True
        )

    @app_commands.checks.has_role(VEGAN_ROLE_ID)
    async def report_message(self, interaction: discord.Interaction, message: discord.Message):
        reporter = interaction.user
        reportee = message.author

        description = '**Von {} ({}, {}) wurde um {} eine Nachricht von {} ({}, {}) im Kanal {} gemeldet:**\n\n{}\n\n{}'.format(
            reporter.mention,
            reporter.display_name,
            reporter.id,
            datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
            reportee.mention,
            reportee.display_name,
            reportee.id,
            message.channel.mention,
            message.content or '*Keine Nachricht*',
            '\n'.join([attachment.url for attachment in message.attachments]) or '*Keine Anhänge*',
        )

        embed = discord.Embed(
            title='Nachricht (ID: {}) gemeldet'.format(message.id),
            description=description,
            timestamp=message.created_at
        )

        embed.set_author(name=reportee.display_name, icon_url=reportee.display_avatar.url)

        url_view = discord.ui.View()
        url_view.add_item(discord.ui.Button(label='Zur Message', style=discord.ButtonStyle.url, url=message.jump_url))
        # url_view.add_item(
        #    discord.ui.Button(label='Ticket erstellen', style=discord.ButtonStyle.primary, custom_id='create_ticket'))

        # Handle report by sending it into a reports channel
        reports_channel_id = await self.configuration_service.get_config_value(interaction.guild_id, ConfigKey.REPORTS_CHANNEL_ID, REPORTS_CHANNEL_ID)
        reports_channel = interaction.guild.get_channel(reports_channel_id)

        if reports_channel is None:
            self.logger.warning(f'Reports channel {reports_channel_id} not found!')

            interaction.response.send_message(
                'Der Reports-Kanal ist nicht vorhanden! Bitte kontaktiere ein Teammitglied.',
                ephemeral=True
            )
            return

        await reports_channel.send(embed=embed, view=url_view)

        # We're sending this response message with ephemeral=True, so only the command executor can see it
        await interaction.response.send_message(
            f'Danke, dass Du die Nachricht von {message.author.mention} gemeldet hast. '
            f'Das Team wird sich das Problem sobald wie möglich anschauen.',
            ephemeral=True
        )

    @app_commands.command(
        description='Einfach ein Test',
    )
    @app_commands.guild_only()
    @app_commands.checks.has_role(VEGAN_ROLE_ID)
    async def test(self, interaction: discord.Interaction):
        await interaction.response.send_modal(TestModal())


    @app_commands.command(
        description='Bewerbe dich für Vegan Safespace',
    )
    @app_commands.guild_only()
    @app_commands.checks.has_role(NEW_USER_ROLE_ID)
    async def apply(self, interaction: discord.Interaction):
        if await self.application_service.has_application(interaction.user.id):
            await interaction.response.send_message(
                f'Du hast bereits eine Bewerbung eingereicht. Bitte warte auf eine Antwort des Teams.',
                ephemeral=True
            )
            return

        await interaction.response.send_modal(ApplicationModal(application_service=self.application_service))


    @app_commands.command(
        name='revoke-application',
        description='Ziehe deine Bewerbung zurück',
    )
    @app_commands.guild_only()
    @app_commands.checks.has_role(NEW_USER_ROLE_ID)
    async def revoke_application(self, interaction: discord.Interaction):
        revoked = await self.application_service.revoke_application(interaction.guild, interaction.user)

        if not revoked:
            await interaction.response.send_message(
                'Du hast keine offene Bewerbung.',
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            'Deine Bewerbung wurde erfolgreich zurückgezogen.',
            ephemeral=True
        )


async def setup(bot: Vale):
    await bot.add_cog(
        UserUtils(
            logger=container.logger(),
            bot=bot,
            application_service=container.application_service(),
            configuration_service=container.configuration_service(),
        )
    )
