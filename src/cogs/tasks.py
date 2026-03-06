from logging import Logger

import discord
from dependency_injector.wiring import inject
from discord.ext import commands, tasks

from src.components.voice_category import VoiceCategory
from src.components.leveling_service import LevelingService
from src.helpers.env import VOICE_CATEGORY_ID, NEW_USER_ROLE_ID
from src.main import container
from src.vale import Vale


class Tasks(commands.Cog):
    @inject
    def __init__(self, logger: Logger, bot: Vale, voice_category: VoiceCategory, leveling_service: LevelingService):
        self.logger = logger
        self.bot = bot
        self.voice_category = voice_category
        self.leveling_service = leveling_service

        self.check_no_roles_assigned.start()
        self.award_voice_xp.start()


    @tasks.loop(hours=24)
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
                self.logger.info(f'Assigned "@{new_user_role.name}" to {count} users.')


    @tasks.loop(minutes=1)
    async def award_voice_xp(self):
        for guild in self.bot.guilds:
            interval = await self.leveling_service.get_voice_interval_minutes(guild.id)
            
            # Every minute we check who is active and increment their counter
            for voice_channel in guild.voice_channels:
                # Check if there's more than 1 person in the channel (not alone)
                if len(voice_channel.members) < 2:
                    continue
                
                for member in voice_channel.members:
                    if member.bot:
                        continue
                    
                    # Not just in voice - check if they are actually "active" (not deafened AND not muted)
                    # We check self_mute/mute because if they are muted they are def not speaking.
                    if member.voice.self_deaf or member.voice.deaf or member.voice.self_mute or member.voice.mute:
                        continue

                    await self.leveling_service.increment_voice_activity(member)

            # We only run the actual award logic if we are on the interval
            if self.award_voice_xp.current_loop % interval != 0 or self.award_voice_xp.current_loop == 0:
                continue

            self.logger.info(f"Awarding voice XP for guild {guild.id}")

            for voice_channel in guild.voice_channels:
                for member in voice_channel.members:
                    if member.bot:
                        continue
                    
                    # Check if they reached the threshold (at least 50% of the interval active)
                    activity_count = await self.leveling_service.get_voice_activity(guild.id, member.id)
                    if activity_count >= (interval / 2):
                        await self.leveling_service.add_voice_xp(member)
            
            # Reset activity for this guild after interval
            await self.leveling_service.reset_voice_activity(guild.id)


    @award_voice_xp.before_loop
    async def before_award_voice_xp(self):
        await self.bot.wait_until_ready()


async def setup(bot: Vale):
    await bot.add_cog(
        Tasks(
            logger=container.logger(),
            bot=bot,
            voice_category=container.voice_category(),
            leveling_service=container.leveling_service(),
        )
    )
