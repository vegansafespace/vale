from collections import defaultdict
from datetime import datetime
import re
from typing import Optional, List, Dict, Union

import discord
from discord import app_commands, Colour, User, Member
from discord.ext import tasks
from discord.utils import MISSING
from dotenv import load_dotenv
import os

load_dotenv()

TOKEN_ENV = os.getenv('DISCORD_TOKEN')
GUILD_ENV: int = int(os.getenv('DISCORD_GUILD'))

APPLICATION_VOICE_WAITING_CHANNEL_ID: int = int(os.getenv('APPLICATION_VOICE_WAITING_CHANNEL_ID'))
APPLICATION_PING_CHANNEL_ID: int = int(os.getenv('APPLICATION_PING_CHANNEL_ID'))

REPORTS_CHANNEL_ID: int = int(os.getenv('REPORTS_CHANNEL_ID'))
ROLE_JUSTIFICATION_CHANNEL_ID: int = int(os.getenv('ROLE_JUSTIFICATION_CHANNEL_ID'))

PRIVATE_CHANNELS_CATEGORY_ID: int = int(os.getenv('PRIVATE_CHANNELS_CATEGORY_ID'))

VOICE_HUB_CATEGORY_ID: int = int(os.getenv('VOICE_HUB_CATEGORY_ID'))
VOICE_HUB_MOVE_ME_CHANNEL_ID: int = int(os.getenv('VOICE_HUB_MOVE_ME_CHANNEL_ID'))
VOICE_HUB_CREATE_CHANNEL_ID: int = int(os.getenv('VOICE_HUB_CREATE_CHANNEL_ID'))
VOICE_HUB_CHANNEL_PREFIX: str = os.getenv('VOICE_HUB_CHANNEL_PREFIX')

VOICE_CATEGORY_ID: int = int(os.getenv('VOICE_CATEGORY_ID'))

GUILD = discord.Object(id=GUILD_ENV)

TEAM_ROLE_ID: int = int(os.getenv('TEAM_ROLE_ID'))
NEW_USER_ROLE_ID: int = int(os.getenv('NEW_USER_ROLE_ID'))
SUPPORT_ROLE_ID: int = int(os.getenv('SUPPORT_ROLE_ID'))
VEGAN_ROLE_ID: int = int(os.getenv('VEGAN_ROLE_ID'))
NON_VEGAN_ROLE_ID: int = int(os.getenv('NON_VEGAN_ROLE_ID'))

TEAM_BANS_CHANNEL_ID: int = int(os.getenv('TEAM_BANS_CHANNEL_ID'))

MAIN_CHAT_CHANNEL_ID: int = int(os.getenv('MAIN_CHAT_CHANNEL_ID'))

# Map which user joined which voice channel and when
# Format: {user_id: {voice_channel_id: datetime}}
voice_channel_join_times = {}


class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        # A CommandTree is a special type that holds all the application command
        # state required to make it work. This is a separate class because it
        # allows all the extra state to be opt-in.
        # Whenever you want to work with application commands, your tree is used
        # to store and work with them.
        # Note: When using commands.Bot instead of discord.Client, the bot will
        # maintain its own tree instead.
        self.tree = app_commands.CommandTree(self)

    # In this basic example, we just synchronize the app commands to one guild.
    # Instead of specifying a guild to every command, we copy over our global commands instead.
    # By doing so, we don't have to wait up to an hour until they are shown to the end-user.
    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=GUILD)
        await self.tree.sync(guild=GUILD)


client = MyClient()


@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')
    check_voice_channels.start()
    # rearrange_voice_channels.start()
    check_no_roles_assigned.start()


@client.event
async def on_member_join(member: discord.Member):
    print(f'{member} (ID: {member.id}) joined the server!')
    new_user_role = discord.utils.get(member.guild.roles, id=NEW_USER_ROLE_ID)
    await member.add_roles(new_user_role)


@tasks.loop(seconds=10)
async def check_voice_channels():
    for guild in client.guilds:
        # Get voice category by id VOICE_CATEGORY_ID
        category = discord.utils.get(guild.categories, id=VOICE_CATEGORY_ID)

        if category is None:
            continue

        voice_channels = [channel for channel in category.channels if
                          isinstance(channel, discord.VoiceChannel) and "#" in channel.name]

        # Gruppiere Kanäle basierend auf dem Namen vor dem "#"
        grouped_channels: Dict[str, List[discord.VoiceChannel]] = {}
        for channel in voice_channels:
            prefix = channel.name.split("#")[0].strip()
            if prefix not in grouped_channels:
                grouped_channels[prefix] = []
            grouped_channels[prefix].append(channel)

        for prefix, channels in grouped_channels.items():
            channels.sort(key=lambda x: int(re.search(r"#(\d+)", x.name).group(1)))  # Sortiere nach der Nummer

            for i, channel in enumerate(channels):
                if len(channel.members) == 0 and len(channels) > 1 and i != 0:
                    # Do only delete channel if channel with i - 1 exists and has members
                    if len(channels[i - 1].members) == 0:
                        await channel.delete()
                elif len(channel.members) != 0 and i == len(channels) - 1:
                    highest_number = int(re.search(r"#(\d+)", channels[-1].name).group(1))
                    new_channel_name = channel.name.replace(f"#{highest_number}", f"#{highest_number + 1}")

                    # Create the new channel
                    new_channel = await category.create_voice_channel(
                        new_channel_name,
                        user_limit=channel.user_limit,
                        overwrites=channel.overwrites,
                        position=channel.position + 1,
                    )

                    # Adjust the position of the new channel
                    await new_channel.edit(
                        position=channel.position + 1,
                    )

                    await rearrange_voice_channels(
                        channel_prefix=new_channel_name.split("#")[0].strip(),
                    )


@tasks.loop(seconds=10)
async def rearrange_voice_channels(channel_prefix: Optional[str]):
    """
    Rearranges voice channels within a given category based on certain conditions.

    :param channel_prefix: (Optional) The prefix of voice channels to consider for rearrangement.
    :return: None
    """
    print("Rearranging voice channels...")

    for guild in client.guilds:
        # Get voice category by id VOICE_CATEGORY_ID
        category = discord.utils.get(guild.categories, id=VOICE_CATEGORY_ID)

        if category is None:
            continue

        voice_channels = [channel for channel in category.channels if
                          isinstance(channel, discord.VoiceChannel) and "#" in channel.name]

        # Gruppiere Kanäle basierend auf dem Namen vor dem "#"
        grouped_channels: Dict[str, List[discord.VoiceChannel]] = {}
        for channel in voice_channels:
            prefix = channel.name.split("#")[0].strip()

            if channel_prefix is not None and channel_prefix is not prefix:
                continue

            if prefix not in grouped_channels:
                grouped_channels[prefix] = []

            grouped_channels[prefix].append(channel)

        for prefix, channels in grouped_channels.items():
            if len(channels) > 1:
                channels.sort(key=lambda x: x.position)
                first_channel_position = channels[0].position
                # Ignore rearranging the first channel
                for i, channel in enumerate(channels[1:], start=1):
                    # Position the voice channel relative to the first voice channel
                    await channel.edit(position=first_channel_position + i)


@tasks.loop(seconds=10)
async def check_no_roles_assigned():
    # Assign @New User role to all users without any role
    for guild in client.guilds:
        count: int = 0
        new_user_role = discord.utils.get(guild.roles, id=NEW_USER_ROLE_ID)

        if new_user_role is None:
            continue

        for member in guild.members:
            if len(member.roles) == 1:
                await member.add_roles(new_user_role)
                count += 1

        if count > 0:
            print(f'Assigned "@{new_user_role.name}" to {count} users.')


# The rename decorator allows us to change the display of the parameter on Discord.
# In this example, even though we use `text_to_send` in the code, the client will use `text` instead.
# Note that other decorators will still refer to it as `text_to_send` in the code.
@client.tree.command()
@app_commands.rename(text_to_send='text')
@app_commands.describe(text_to_send='Text to send in the current channel')
async def send(interaction: discord.Interaction, text_to_send: str):
    """Sends the text into the current channel."""
    await interaction.response.send_message(text_to_send)


# To make an argument optional, you can either give it a supported default argument
# or you can mark it as Optional from the typing standard library. This example does both.
@client.tree.command()
@app_commands.describe(
    member='The member you want to get the joined date from; defaults to the user who uses the command')
async def joined(interaction: discord.Interaction, member: Optional[discord.Member] = None):
    """Says when a member joined."""
    # If no member is explicitly provided then we use the command user here
    member = member or interaction.user

    # The format_dt function formats the date time into a human readable representation in the official client
    await interaction.response.send_message(
        f'{member} joined {discord.utils.format_dt(member.joined_at)}', ephemeral=True
    )


@client.tree.command(
    description='Gibt einer Person die @Vegan Rolle',
)
@app_commands.describe(
    member='Eine Person die @Vegan bekommen soll',
    reason='Der Grund warum die Person @Vegan bekommen soll',
)
async def vegan(interaction: discord.Interaction, member: discord.Member, reason: str):
    vegan_role = discord.utils.get(interaction.guild.roles, id=VEGAN_ROLE_ID)
    non_vegan_role = discord.utils.get(interaction.guild.roles, id=NON_VEGAN_ROLE_ID)

    await _assign_initial_role(interaction, member, vegan_role, non_vegan_role, reason)


# @client.tree.command(
#    description='Gibt einer Person die @Nicht Vegan Rolle',
# )
# @app_commands.describe(
#    member='Eine Person die @Nicht Vegan bekommen soll',
#    reason='Der Grund warum die Person @Nicht vegan bekommen soll',
# )
# async def nonvegan(interaction: discord.Interaction, member: discord.Member, reason: str):
#    non_vegan_role = discord.utils.get(interaction.guild.roles, id=NON_VEGAN_ROLE_ID)
#    vegan_role = discord.utils.get(interaction.guild.roles, id=VEGAN_ROLE_ID)
#
#    await _assign_initial_role(interaction, member, non_vegan_role, vegan_role, reason)


async def _assign_initial_role(
        interaction: discord.Interaction,
        member: discord.Member,
        role_to_assign: discord.Role,
        role_to_remove: discord.Role,
        reason: str,
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

    await _report_role_assignment(interaction, executor, member, role_to_assign, reason)
    await _welcome_user(interaction, executor, member, role_to_assign)

    await interaction.response.send_message('Du hast {} die Rolle {} zugewiesen!'.format(
        member.mention,
        role_to_assign.mention
    ), ephemeral=True)


async def _report_role_assignment(
        interaction: discord.Interaction,
        executor: Union[User, Member],
        member: discord.Member,
        assigned_role: discord.Role,
        reason: str,
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
        reason
    )

    embed = discord.Embed(
        title='{} freigeschaltet'.format(member.display_name),
        description=description,
        timestamp=interaction.created_at,
        colour=assigned_role.colour
    )

    embed.set_thumbnail(url=member.display_avatar.url)

    # Handle report by sending it into a role justification channel
    role_justification_channel = interaction.guild.get_channel(ROLE_JUSTIFICATION_CHANNEL_ID)

    await role_justification_channel.send(embed=embed)


async def _welcome_user(
        interaction: discord.Interaction,
        executor: Union[User, Member],
        member: discord.Member,
        assigned_role: discord.Role,
):
    embed = discord.Embed(
        title='Willkommen {}!'.format(member.display_name),
        description='{} wurde soeben freigeschaltet und ist jetzt Teil der Vegan Safespace Community!'.format(
            member.display_name,
        ),
        colour=assigned_role.colour,
    )

    embed.set_thumbnail(url=member.display_avatar.url)

    embed.set_footer(
        text='Von {} freigeschaltet!'.format(executor.display_name),
        icon_url=executor.display_avatar.url,
    )

    # Welcome member to everyone
    main_chat_channel = interaction.guild.get_channel(MAIN_CHAT_CHANNEL_ID)

    await main_chat_channel.send(
        content="Willkommen {} auf Vegan Safespace!".format(member.mention),
        embed=embed,
    )


@client.tree.command()
@app_commands.describe(
    user=f'Die Person, die gebannt werden soll',
    reason=f'Der Grund warum die Person gebannt werden soll',
    delete_messages=f'Ob die Nachrichten der Person gelöscht werden sollen'
)
async def ban(interaction: discord.Interaction, user: discord.User, reason: str, delete_messages: bool = False):
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

    await interaction.response.send_message('Du hast {} gebannt!'.format(
        user.mention,
    ), ephemeral=True)


@client.tree.command()
@app_commands.describe()
async def verify(interaction: discord.Interaction):
    button = discord.ui.Button(
        label='Ich bin ein Mensch!',
        style=discord.ButtonStyle.primary,
        custom_id='verify'
    )

    async def check_button(i: discord.Interaction):
        await i.response.send_message(
            'Danke für deine Bestätigung!',
            ephemeral=True
        )

    button.callback = check_button

    view = discord.ui.View(timeout=None)
    view.add_item(button)

    await interaction.response.send_message(
        'Bitte bestätige, dass du ein Mensch bist!',
        ephemeral=True,
        view=view
    )


# A Context Menu command is an app command that can be run on a member or on a message by
# accessing a menu within the client, usually via right clicking.
# It always takes an interaction as its first parameter and a Member or Message as its second parameter.

# This context menu command only works on members
@client.tree.context_menu(name='Show Join Date')
async def show_join_date(interaction: discord.Interaction, member: discord.Member):
    # The format_dt function formats the date time into a human readable representation in the official client
    await interaction.response.send_message(
        f'{member} joined at {discord.utils.format_dt(member.joined_at)}', ephemeral=True
    )


# This context menu command only works on messages
@client.tree.context_menu(name='Dem Team melden')
async def report_message(interaction: discord.Interaction, message: discord.Message):
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


@client.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    # Check if joined or left channel
    if before.channel == after.channel:
        return

    # Check if user joined the move-me channel
    if after.channel is not None and after.channel.id == VOICE_HUB_MOVE_ME_CHANNEL_ID:
        await _on_join_voice_hub_move_me_channel(member, before, after)

    # Check if user joined the create channel
    if after.channel is not None and after.channel.id == VOICE_HUB_CREATE_CHANNEL_ID:
        await _on_join_voice_hub_create_channel(member, before, after)

    # Check if user joined the application waiting room
    if after.channel is not None and after.channel.id == APPLICATION_VOICE_WAITING_CHANNEL_ID:
        await _on_join_application_waiting_room(member, before, after)

    # Check if user joined any of the voice channels in the voice category
    if after.channel is not None and after.channel.category.id == VOICE_CATEGORY_ID:
        await _on_join_voice_channel(member, before, after)

    # Check if user joined any of the voice channels in the voice category
    if before.channel is not None and before.channel.category.id == VOICE_CATEGORY_ID:
        await _on_leave_voice_channel(member, before, after)

    # Check if user left the application waiting room
    if before.channel is not None and before.channel.id == APPLICATION_VOICE_WAITING_CHANNEL_ID:
        await _on_leave_application_waiting_room(member, before, after)

    # Check if user left a voice hub channel
    if before.channel is not None and before.channel.category_id == VOICE_HUB_CATEGORY_ID:
        # Check if is voice hub voice channel with VOICE_HUB_CHANNEL_PREFIX
        if before.channel.name.startswith(VOICE_HUB_CHANNEL_PREFIX):
            # Check if user is the only one left in the channel
            if len(before.channel.members) == 0:
                # Delete channel
                await before.channel.delete()


async def _on_join_voice_hub_move_me_channel(
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState
):
    # Get all voice channels in the category
    channels = after.channel.category.voice_channels

    # Remove the move me and create channels
    channels.remove(after.channel.guild.get_channel(VOICE_HUB_MOVE_ME_CHANNEL_ID))
    channels.remove(after.channel.guild.get_channel(VOICE_HUB_CREATE_CHANNEL_ID))

    select = discord.ui.Select(
        options=[
            discord.SelectOption(label=channel.name, value=str(channel.id))
            for channel in channels
        ],
        placeholder='Kanal wählen',
        custom_id='move_user'
    )

    async def select_callback(i1: discord.Interaction):
        if i1.user.id != member.id:
            await i1.response.send_message(
                f'Diese Auswahl ist nicht für Dich gedacht.',
                ephemeral=True,
                delete_after=120.0
            )
            return

        # Delete message
        await i1.message.delete()

        # Get selected channel
        selected_channel_id = int(i1.data['values'][0])
        selected_channel = after.channel.guild.get_channel(selected_channel_id)

        # Get channel members with explicit permission for the selected channel to read messages
        channel_readers = [
            reader for reader in selected_channel.members if
            selected_channel.permissions_for(reader).read_messages and not reader.bot
        ]

        button = discord.ui.Button(
            label=f'{member.display_name} reinziehen',
            style=discord.ButtonStyle.primary,
            custom_id='move_user_accept'
        )

        async def button_callback(i2: discord.Interaction):
            # Give user permissions to read messages in the selected channel
            overwrite = discord.PermissionOverwrite()

            overwrite.view_channel = True
            overwrite.moderate_members = False
            overwrite.connect = True
            overwrite.speak = True
            overwrite.read_messages = True
            overwrite.read_message_history = True
            overwrite.send_messages = True

            await selected_channel.set_permissions(
                member,
                overwrite=overwrite,
            )

            # Move user into the new channel
            await member.move_to(selected_channel)

            # Delete message
            await i2.message.delete()

        button.callback = button_callback

        view = discord.ui.View(timeout=None)
        view.add_item(button)

        reader_mentions = ', '.join([reader.mention for reader in channel_readers])
        reader_break = '\n\n' if reader_mentions else ''

        await selected_channel.send(
            f'{reader_mentions}{reader_break}{member.mention} möchte gerne in diesen Kanal gezogen werden. '
            f'Bitte bestätige mit dem Button, wenn du das erlauben möchtest.',
            view=view,
            delete_after=120.0
        )

        await i1.response.send_message(
            f'Top! Eine Person vom Kanal {selected_channel.mention} zieht Dich bestimmt gleich rein.',
            ephemeral=True,
            delete_after=120.0
        )

    select.callback = select_callback

    # Send message to user in the move-me channel allowing him to choose a channel
    await after.channel.send(
        f'{member.mention} Bitte wähle einen Kanal aus, dem Du gerne beitreten möchtest:',
        view=discord.ui.View(timeout=None).add_item(select),
        delete_after=120.0
    )


async def _on_join_voice_hub_create_channel(
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState
):
    channel = after.channel

    vegan_role = discord.utils.get(channel.guild.roles, id=VEGAN_ROLE_ID)
    team_role = discord.utils.get(channel.guild.roles, id=TEAM_ROLE_ID)

    overwrites = {
        channel.guild.default_role: discord.PermissionOverwrite(
            view_channel=False,
            # moderate_members=False,
            connect=False,
            speak=False,
            read_messages=False,
            read_message_history=False,
            send_messages=False,
        ),
        member: discord.PermissionOverwrite(
            view_channel=True,
            # moderate_members=True,
            connect=True,
            speak=True,
            read_messages=True,
            read_message_history=True,
            send_messages=True,
        ),
        vegan_role: discord.PermissionOverwrite(
            view_channel=True,
            # moderate_members=False,
            connect=False,
            speak=False,
            read_messages=True,
            read_message_history=False,
            send_messages=False,
        ),
        team_role: discord.PermissionOverwrite(
            view_channel=True,
            # moderate_members=True,
            connect=True,
            speak=True,
            read_messages=True,
            read_message_history=True,
            send_messages=True,
        ),
    }

    # Create voice channel
    voice_channel = await channel.category.create_voice_channel(
        f'{VOICE_HUB_CHANNEL_PREFIX}{member.name.lower().replace(" ", "-")}',
        overwrites=overwrites,
    )

    await member.move_to(voice_channel)


@client.tree.command(
    description='Person aus eigenem Voice Channel kicken',
)
@app_commands.describe(
    member='Die Person, die gekickt werden soll',
)
async def voice_kick(interaction: discord.Interaction, member: discord.Member):
    # Check if user is in a voice hub channel
    if interaction.channel.category_id != VOICE_HUB_CATEGORY_ID or not interaction.channel.name.startswith(
            VOICE_HUB_CHANNEL_PREFIX):
        await interaction.response.send_message(
            f'Du kannst nur Personen aus einem Voice Hub Channel kicken!',
            ephemeral=True
        )
        return

    # Check if user is in a voice hub channel with VOICE_HUB_CHANNEL_PREFIX
    if not member.voice.channel.name.startswith(VOICE_HUB_CHANNEL_PREFIX):
        await interaction.response.send_message(
            f'Die Person ist nicht in einem Voice Hub Channel!',
            ephemeral=True
        )
        return

    # Check if user is in the same voice hub channel
    if member.voice.channel != interaction.channel:
        await interaction.response.send_message(
            f'Die Person ist nicht in Deinem Voice Hub Channel!',
            ephemeral=True
        )
        return

    #


async def _on_join_application_waiting_room(
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState
):
    channel = after.channel

    application_ping_channel = channel.guild.get_channel(APPLICATION_PING_CHANNEL_ID)
    support_role = discord.utils.get(channel.guild.roles, id=SUPPORT_ROLE_ID)

    # Check if any support member is online
    # if not any([supporter.status != discord.Status.offline for supporter in support_role.members]):
    #     # Send message to user that no support member is online
    #     await channel.send(
    #         f'{member.mention} Es ist leider gerade kein Supporter online. Bitte versuche es später noch einmal.',
    #         delete_after=30.0
    #     )
    #
    #     return

    # Button to instantly join a free application room within the category and move the user into it
    button = discord.ui.Button(
        label='Zum Support',
        style=discord.ButtonStyle.primary,
        custom_id='join_application_room'
    )

    async def button_callback(i: discord.Interaction):
        # Delete message
        await i.message.delete()

        # Create voice channel for @Support role and user that joined the waiting room
        voice_channel = await channel.category.create_voice_channel(
            f'bewerbung-{member.display_name.lower().replace(" ", "-")}',
            user_limit=2,
        )

        can_not_see_overwrite = discord.PermissionOverwrite()

        can_not_see_overwrite.view_channel = False
        can_not_see_overwrite.connect = False
        can_not_see_overwrite.speak = False
        can_not_see_overwrite.read_messages = False
        can_not_see_overwrite.send_messages = False

        await voice_channel.set_permissions(
            channel.guild.default_role,
            overwrite=can_not_see_overwrite,
        )

        can_see_overwrite = discord.PermissionOverwrite()

        can_see_overwrite.view_channel = True
        can_see_overwrite.connect = True
        can_see_overwrite.speak = True
        can_see_overwrite.read_messages = True
        can_see_overwrite.send_messages = True

        await voice_channel.set_permissions(
            member,
            overwrite=can_see_overwrite,
        )

        await voice_channel.set_permissions(
            support_role,
            overwrite=can_see_overwrite,
        )

        await member.move_to(voice_channel)
        await i.user.move_to(voice_channel)

    button.callback = button_callback

    # Send message to application ping channel that a new user joined the waiting room
    await application_ping_channel.send(
        f'**{support_role.mention}**: '
        f'{member.mention} ist dem Bewerbungs-Warteraum beigetreten. Drück den Button, '
        f'um die Person in einen neuen Support-Raum zu ziehen und mit dem Bewerbungsgespräch zu beginnen.',
        view=discord.ui.View(timeout=None).add_item(button),
        delete_after=8 * 60 * 60.0  # 8 hours as a fallback
    )


async def _on_join_voice_channel(
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState
):
    # Make sure channel name contains a "#"
    if "#" not in after.channel.name:
        return

    # Sent notification in channel that user joined
    await after.channel.send(
        f'{member.display_name} ist dem Kanal beigetreten.',
        silent=True,
        delete_after=30 * 60.0  # 30 minutes
    )


async def _on_leave_voice_channel(
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState
):
    # Make sure channel name contains a "#"
    if "#" not in before.channel.name:
        return

    # Sent notification in channel that user left
    await before.channel.send(
        f'{member.display_name} hat den Kanal verlassen.',
        silent=True,
        delete_after=30 * 60.0  # 30 minutes
    )


async def _on_leave_application_waiting_room(
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState
):
    channel = before.channel
    application_ping_channel = channel.guild.get_channel(APPLICATION_PING_CHANNEL_ID)

    # Remove ping message if user left the application waiting room
    async for message in application_ping_channel.history(limit=100):
        # Check if message mentions the user
        if member.mention in message.content:
            # Delete message
            await message.delete()
            break


# @client.event
# async def on_message(message: discord.Message):
#    # Get executor
#    executor = message.author
#
#    # Format `!vegan @user <reason>`
#    if message.content.startswith('!vegan'):
#        # Delete message
#        await message.delete()
#
#        # Exit if user is not in `@Team` or `@Support` role
#        if client.team_role.name not in [role.name for role in executor.roles] \
#                and client.support_role.name not in [role.name for role in executor.roles]:
#            await message.channel.send(
#                f"{executor.mention} Du hast kein Teammitglied!",
#                delete_after=5.0,
#            )
#            return
#
#        # Check if `message.mentions` is not empty
#        if not message.mentions:
#            await message.channel.send(
#                f"{executor.mention} Du musst ein:eine Nutzer:in erwähnen (`!vegan @user`)!",
#                delete_after=5.0,
#            )
#            return
#
#        # Get mentioned user, if there is none, return with error message
#        user = message.mentions[0]
#
#        if not user:
#            await message.channel.send(
#                f"{executor.mention} Du musst ein:eine Nutzer:in erwähnen (`!vegan @user`)!",
#                delete_after=5.0,
#            )
#            return
#
#        ## Get reason
#        # reason = message.content.split(' ', 2)[2]
#        #
#        ## Check reason
#        # if not reason:
#        #    await message.channel.send(
#        #        f"{executor.mention} Du musst einen Grund angeben (`!vegan @user <reason>`)!",
#        #        delete_after=5.0,
#        #    )
#        #    return
#
#        messages: [discord.Message]
#
#        # Get messages from channel if channel name begins with `bewerbung-`
#        if message.channel.name.startswith('bewerbung-'):
#            messages = [channel_message async for channel_message in message.channel.history(limit=123)]
#
#        await user.add_roles(client.based_role)
#        await user.add_roles(client.vegan_role)
#
#        if client.non_vegan_role in user.roles:
#            await user.remove_roles(client.non_vegan_role)
#
#        await message.channel.send(f"{user.mention} hat jetzt die \"Vegan\"-Rolle!")
#
#    if message.content.startswith('!nonvegan'):
#        # Delete message
#        await message.delete()
#
#        # Exit if user is not in `@Team` or `@Support` role
#        if client.team_role not in [role.name for role in executor.roles] \
#                and client.support_role not in [role.name for role in executor.roles]:
#            await message.channel.send(
#                f"{executor.mention} Du hast kein Teammitglied!",
#                delete_after=5.0,
#            )
#            return
#
#        # Check if `message.mentions` is not empty
#        if not message.mentions:
#            await message.channel.send(
#                f"{executor.mention} Du musst ein:eine Nutzer:in erwähnen (`!nonvegan @user`)!",
#                delete_after=5.0,
#            )
#            return
#
#        # Get mentioned user, if there is none, return with error message
#        user = message.mentions[0]
#
#        if not user:
#            await message.channel.send(
#                f"{executor.mention} Du musst ein:eine Nutzer:in erwähnen (`!nonvegan @user`)!",
#                delete_after=5.0,
#            )
#            return
#
#        await user.add_roles(client.based_role)
#        await user.add_roles(client.non_vegan_role)
#
#        if client.vegan_role in user.roles:
#            await user.remove_roles(client.vegan_role)
#
#        await message.channel.send(f"{user.mention} hat jetzt die \"Nicht Vegan\"-Rolle!")


client.run(TOKEN_ENV)
