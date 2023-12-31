import discord

from src.helpers.env import APPLICATION_PING_CHANNEL_ID, SUPPORT_ROLE_ID


class Application:
    async def on_join_waiting_room(
            self,
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

    async def on_leave_waiting_room(
            self,
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

    async def on_leave_application_voice(
            self,
            member: discord.Member,
            before: discord.VoiceState,
            after: discord.VoiceState
    ):
        left_application_channel = before.channel.name.startswith('bewerbung-')
        channel_is_empty = len(before.channel.members) == 0

        # Check if left channel that is prefixed with "bewerbung-" and if user is the only one left in the channel
        if left_application_channel and channel_is_empty:
            # Delete channel
            await before.channel.delete()
