import re
from typing import Dict, List

import discord
from dependency_injector.wiring import inject
from discord.ext import commands, tasks

from src.components.voice_category import VoiceCategory
from src.helpers.env import VOICE_CATEGORY_ID, NEW_USER_ROLE_ID
from src.main import container
from src.vale import Vale


class Tasks(commands.Cog):
    @inject
    def __init__(self, bot: Vale, voice_category: VoiceCategory):
        self.bot = bot

        self.voice_category = voice_category

        self.check_voice_channels.start()
        self.check_no_roles_assigned.start()

    @tasks.loop(seconds=10)
    async def check_voice_channels(self):
        for guild in self.bot.guilds:
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

                        await self.voice_category.rearrange_voice_channels(
                            bot=self.bot,
                            channel_prefix=new_channel_name.split("#")[0].strip(),
                        )

    @tasks.loop(seconds=10)
    async def check_no_roles_assigned(self):
        # Assign @New User role to all users without any role
        for guild in self.bot.guilds:
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


async def setup(bot: Vale):
    bot_a = bot
    bot_b = container.bot()

    await bot.add_cog(
        Tasks(
            bot,
            voice_category=container.voice_category(),
        )
    )
