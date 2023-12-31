import discord

from src.helpers.env import VOICE_HUB_MOVE_ME_CHANNEL_ID, VOICE_HUB_CREATE_CHANNEL_ID, VEGAN_ROLE_ID, TEAM_ROLE_ID, \
    VOICE_HUB_CHANNEL_PREFIX


class VoiceHub:

    async def on_join_move_me_channel(
            self,
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
        )

    async def on_leave_move_me_channel(
            self,
            member: discord.Member,
            before: discord.VoiceState,
            after: discord.VoiceState
    ):
        channel = before.channel

        # Remove ping message if user left the move me channel
        async for message in channel.history(limit=100):
            # Check if message mentions the user
            if member.mention in message.content:
                # Delete message
                await message.delete()
                break

    async def on_join_create_channel(
            self,
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

    async def on_leave_hub_channel(
            self,
            member: discord.Member,
            before: discord.VoiceState,
            after: discord.VoiceState
    ):
        # Check if is voice hub voice channel with VOICE_HUB_CHANNEL_PREFIX
        if before.channel.name.startswith(VOICE_HUB_CHANNEL_PREFIX):
            # Check if user is the only one left in the channel
            if len(before.channel.members) == 0:
                # Delete channel
                await before.channel.delete()
