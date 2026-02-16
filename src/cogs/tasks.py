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

        self.check_no_roles_assigned.start()


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
                print(f'Assigned "@{new_user_role.name}" to {count} users.')


async def setup(bot: Vale):
    await bot.add_cog(
        Tasks(
            bot,
            voice_category=container.voice_category(),
        )
    )
