from typing import Union, Optional

import discord
from discord import app_commands, User, Member
from discord.app_commands import CommandInvokeError
from discord.ext import commands
from discord.utils import MISSING

from src.helpers.env import VEGAN_ROLE_ID, NON_VEGAN_ROLE_ID, TEAM_ROLE_ID, NEW_USER_ROLE_ID, \
    ROLE_JUSTIFICATION_CHANNEL_ID, MAIN_CHAT_CHANNEL_ID, TEAM_BANS_CHANNEL_ID, NON_VEGAN_MAIN_CHAT_CHANNEL_ID, \
    OUTREACH_ROLE_ID
from src.vale import Vale


class TeamUtils(commands.Cog):
    def __init__(self, bot: Vale):
        self.bot = bot

    @app_commands.command(
        description='Eine Person bannen',
    )
    @app_commands.describe(
        user=f'Die Person, die gebannt werden soll',
        reason=f'Der Grund warum die Person gebannt werden soll',
        delete_messages=f'Ob die Nachrichten der Person gelöscht werden sollen'
    )
    @app_commands.guild_only()
    @app_commands.checks.has_role(TEAM_ROLE_ID)
    async def ban(self, interaction: discord.Interaction, user: discord.User, reason: str,
                  delete_messages: bool = False):
        executor = interaction.user

        team_role = discord.utils.get(interaction.guild.roles, id=TEAM_ROLE_ID)

        # Exit if user is not in `@Team`
        if team_role.name not in [role.name for role in executor.roles]:
            await interaction.response.send_message("Du hast kein Teammitglied!", ephemeral=True)
            return

        try:
            await interaction.guild.ban(
                user,
                reason=reason,
                delete_message_days=365 if delete_messages else MISSING,
                delete_message_seconds=0 if delete_messages else MISSING,
            )
        except discord.app_commands.errors.TransformerError:
            # User may not be in the guild or is not a member
            pass

        description = '{} ({}, {}) wurde von {} ({}, {}) gebannt.\n\n' \
                      '**Grund:**\n\n' \
                      '{}\n\n' \
                      '{}'.format(
            user.mention,
            user.display_name,
            user.id,
            executor.mention,
            executor.display_name,
            executor.id,
            reason,
            delete_messages and '**Die Nachrichten der Person wurden gelöscht.**' or '**Die Nachrichten der Person wurden nicht gelöscht.**'
        )

        embed = discord.Embed(
            title='Person gebannt via `/ban`',
            description=description,
            timestamp=interaction.created_at
        )

        embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)

        # Handle report by sending it into a role justification channel
        bans_channel = interaction.guild.get_channel(TEAM_BANS_CHANNEL_ID)

        await bans_channel.send(embed=embed)

        has_sent_dm = await self._send_ban_dm(interaction, user, reason)

        await interaction.response.send_message('Du hast {} gebannt! ({})'.format(
            user.mention,
            has_sent_dm and 'DM gesendet.' or 'Keine DM gesendet.'
        ), ephemeral=True)

    async def _send_ban_dm(self, interaction: discord.Interaction, user: discord.User, reason: str) -> bool:
        try:
            # Check if user is member of guild
            member = interaction.guild.get_member(user.id)

            if member is None:
                return False

            dm_channel = await member.create_dm()

            dm_embed = discord.Embed(
                title=f'{interaction.guild.name} - Ausschluss',
                description=reason,
                timestamp=interaction.created_at
            )

            if interaction.guild.icon is not None:
                dm_embed.set_thumbnail(url=interaction.guild.icon.url)

            await dm_channel.send(embed=dm_embed)

            return True
        except CommandInvokeError:
            # User may not be in the guild, is not a member or has DMs disabled
            pass
        except Exception as e:
            print(e)
            pass

        return False

    @app_commands.command(
        description='Einer Person die Vegan-Rolle vergeben',
    )
    @app_commands.describe(
        member='Eine Person die die Vegan-Rolle bekommen soll',
        reason='Der Grund warum die Person die Vegan-Rolle bekommen soll',
    )
    @app_commands.guild_only()
    @app_commands.checks.has_role(TEAM_ROLE_ID)
    async def vegan(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        vegan_role = discord.utils.get(interaction.guild.roles, id=VEGAN_ROLE_ID)
        non_vegan_role = discord.utils.get(interaction.guild.roles, id=NON_VEGAN_ROLE_ID)

        await self._assign_initial_role(interaction, member, vegan_role, non_vegan_role, reason)

    @app_commands.command(
        name='non-vegan',
        description='Einer Person die "Auf dem Weg"-Rolle vergeben',
    )
    @app_commands.describe(
        member='Eine Person die die "Auf dem Weg"-Rolle bekommen soll',
        reason='Optionaler Grund warum die Person die "Auf dem Weg"-Rolle bekommen soll',
    )
    @app_commands.guild_only()
    @app_commands.checks.has_role(TEAM_ROLE_ID)
    async def non_vegan(self, interaction: discord.Interaction, member: discord.Member, reason: Optional[str] = None):
        non_vegan_role = discord.utils.get(interaction.guild.roles, id=NON_VEGAN_ROLE_ID)
        vegan_role = discord.utils.get(interaction.guild.roles, id=VEGAN_ROLE_ID)

        await self._assign_initial_role(interaction, member, non_vegan_role, vegan_role, reason)

    async def _assign_initial_role(
            self,
            interaction: discord.Interaction,
            member: discord.Member,
            role_to_assign: discord.Role,
            role_to_remove: discord.Role,
            reason: Optional[str] = None,
    ):
        executor = interaction.user

        team_role = discord.utils.get(interaction.guild.roles, id=TEAM_ROLE_ID)

        # Exit if user is not in `@Team` or `@Support` role
        if team_role.name not in [role.name for role in executor.roles]:
            await interaction.response.send_message("Du bist kein Teammitglied!", ephemeral=True)
            return

        new_user_role = discord.utils.get(member.guild.roles, id=NEW_USER_ROLE_ID)

        # Check if member can view current channel
        if not interaction.channel.permissions_for(member).read_messages:
            await interaction.response.send_message(
                f'{member.mention} kann diesen Kanal nicht sehen! Bitte verifiziere die Person in einem Kanal, den sie sehen kann.',
                ephemeral=True
            )
            return

        await member.add_roles(role_to_assign)
        await member.remove_roles(new_user_role)

        if role_to_remove in member.roles:
            await member.remove_roles(role_to_remove)

        # Send message to member in channel
        await interaction.channel.send(
            f'{member.mention} hat die Rolle @{role_to_assign.name} bekommen!'
        )

        await self._report_role_assignment(interaction, executor, member, role_to_assign, reason)
        await self._welcome_user(interaction, executor, member, role_to_assign)

        await interaction.response.send_message('Du hast {} die Rolle {} zugewiesen!'.format(
            member.mention,
            role_to_assign.mention
        ), ephemeral=True)

    async def _report_role_assignment(
            self,
            interaction: discord.Interaction,
            executor: Union[User, Member],
            member: discord.Member,
            assigned_role: discord.Role,
            reason: Optional[str] = None,
    ):
        description = '{} ({}, {}) hat von {} ({}, {}) die Rolle {} zugewiesen bekommen.\n\n' \
                      '**Grund:**\n' \
                      '{}'.format(
            member.mention,
            member.display_name,
            member.id,
            executor.mention,
            executor.display_name,
            executor.id,
            assigned_role.mention,
            reason or 'Kein Grund angegeben.'
        )

        embed = discord.Embed(
            title='Rollenvergabe {}'.format(member.display_name),
            description=description,
            timestamp=interaction.created_at,
            colour=assigned_role.colour
        )

        embed.set_thumbnail(url=member.display_avatar.url)

        # Handle report by sending it into a role justification channel
        role_justification_channel = interaction.guild.get_channel(ROLE_JUSTIFICATION_CHANNEL_ID)

        await role_justification_channel.send(embed=embed)

    async def _welcome_user(
            self,
            interaction: discord.Interaction,
            executor: Union[User, Member],
            member: discord.Member,
            assigned_role: discord.Role,
    ):
        if assigned_role.id == VEGAN_ROLE_ID:
            await self._welcome_vegan(assigned_role, executor, interaction, member)
            return

        if assigned_role.id == NON_VEGAN_ROLE_ID:
            await self._welcome_non_vegan(assigned_role, executor, interaction, member)
            return

    async def _welcome_vegan(self, assigned_role, executor, interaction, member):
        embed = discord.Embed(
            title='Willkommen {}!'.format(member.display_name),
            description='{} wurde soeben freigeschaltet und ist jetzt Teil der Vegan Safespace Community!'.format(
                member.display_name,
            ),
            colour=assigned_role.colour,
        )

        embed.set_thumbnail(url=member.display_avatar.url)

        embed.set_footer(
            text='Von {} freigeschaltet'.format(executor.display_name),
            icon_url=executor.display_avatar.url,
        )

        # Welcome member to everyone
        main_chat_channel = interaction.guild.get_channel(MAIN_CHAT_CHANNEL_ID)

        await main_chat_channel.send(
            content="Willkommen {} auf Vegan Safespace!".format(member.mention),
            embed=embed,
        )

    async def _welcome_non_vegan(self, assigned_role, executor, interaction, member):
        embed = discord.Embed(
            title='Hey {}! Willkommen!'.format(member.display_name),
            description='{} wurde soeben für den "Auf dem Weg"-Space freigeschaltet!'.format(
                member.display_name,
            ),
            colour=assigned_role.colour,
        )

        embed.set_thumbnail(url=member.display_avatar.url)

        embed.set_footer(
            text='Rolle von {} vergeben'.format(executor.display_name),
            icon_url=executor.display_avatar.url,
        )

        # Welcome member to everyone in the non-vegan channel
        non_vegan_main_chat_channel = interaction.guild.get_channel(NON_VEGAN_MAIN_CHAT_CHANNEL_ID)

        outreach_role = discord.utils.get(member.guild.roles, id=OUTREACH_ROLE_ID)

        await non_vegan_main_chat_channel.send(
            content="Hey {}! Willkommen! ({})".format(member.mention, outreach_role.mention),
            embed=embed,
        )


async def setup(bot: Vale):
    await bot.add_cog(
        TeamUtils(
            bot,
        )
    )
