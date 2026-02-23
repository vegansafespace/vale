import re
from logging import Logger
from typing import Optional, Dict, List

import discord

from src.helpers.env import VOICE_CATEGORY_ID, DISCORD_GUILD
from src.helpers.config_keys import ConfigKey
from src.components.configuration_service import ConfigurationService
from src.vale import Vale


class VoiceCategory:
    def __init__(self, logger: Logger, configuration_service: ConfigurationService):
        self.logger = logger
        self.configuration_service = configuration_service

    async def on_join(
            self,
            member: discord.Member,
            before: discord.VoiceState,
            after: discord.VoiceState,
            bot: Vale
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

        await self._check_scaling(after.channel.category, bot)

    async def on_leave(
            self,
            member: discord.Member,
            before: discord.VoiceState,
            after: discord.VoiceState,
            bot: Vale
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

        await self._check_scaling(before.channel.category, bot)

    async def _check_scaling(self, category: discord.CategoryChannel, bot: Vale):
        voice_category_id = await self.configuration_service.get_config_value(category.guild.id, ConfigKey.VOICE_CATEGORY_ID, VOICE_CATEGORY_ID)

        if category is None or category.id != voice_category_id:
            return

        voice_channels = [channel for channel in category.channels if
                          isinstance(channel, discord.VoiceChannel) and "#" in channel.name]

        # Group channels based on the name before "#"
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

                    await self.rearrange_voice_channels(
                        bot=bot,
                        channel_prefix=new_channel_name.split("#")[0].strip(),
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
        voice_category_id = await self.configuration_service.get_config_value(guild.id, ConfigKey.VOICE_CATEGORY_ID, VOICE_CATEGORY_ID)
        category = discord.utils.get(guild.categories, id=voice_category_id)

        if category is None:
            self.logger.warning(f"Voice category {voice_category_id} not found for guild {guild.id}.")
            return

        voice_channels = [channel for channel in category.channels if
                          isinstance(channel, discord.VoiceChannel) and "#" in channel.name]

        # Gruppiere Kanäle basierend auf dem Namen vor dem "#"
        grouped_channels: Dict[str, List[discord.VoiceChannel]] = {}

        for channel in voice_channels:
            prefix = channel.name.split("#")[0].strip()

            if channel_prefix is not None and channel_prefix != prefix:
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
