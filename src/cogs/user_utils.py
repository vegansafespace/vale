from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from src.helpers.env import VEGAN_ROLE_ID, REPORTS_CHANNEL_ID
from src.vale import Vale


class UserUtils(commands.Cog):
    def __init__(self, bot: Vale):
        self.bot = bot

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
        reports_channel = interaction.guild.get_channel(REPORTS_CHANNEL_ID)

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
    @app_commands.describe(
        user=f'Eine Person, die erwähnt werden soll'
    )
    @app_commands.guild_only()
    @app_commands.checks.has_role(VEGAN_ROLE_ID)
    async def test(self, interaction: discord.Interaction, user: discord.User):
        await interaction.response.send_message('Du hast {} erwähnt!'.format(
            user.mention,
        ), ephemeral=True)


async def setup(bot: Vale):
    await bot.add_cog(
        UserUtils(
            bot,
        )
    )
