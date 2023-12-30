from typing import Optional, Dict, List

import discord

from src.helpers.env import VOICE_CATEGORY_ID, DISCORD_GUILD
from src.vale import Vale


class VoiceCategory:
    async def on_join(
            self,
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

    async def on_leave(
            self,
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

    async def rearrange_voice_channels(self, bot: Vale, channel_prefix: Optional[str]):
        """
        Rearranges voice channels within a given category based on certain conditions.

        :param bot: Injected bot that is currently used.
        :param channel_prefix: (Optional) The prefix of voice channels to consider for rearrangement.
        :return: None
        """

        guild = bot.get_guild(DISCORD_GUILD)

        if guild is None:
            return

        # Get voice category by id VOICE_CATEGORY_ID
        category = discord.utils.get(guild.categories, id=VOICE_CATEGORY_ID)

        if category is None:
            return

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
