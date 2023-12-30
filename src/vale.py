from pathlib import Path

import discord
from discord.ext import commands

from src.helpers.env import DISCORD_GUILD


class Vale(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.guild_messages = True
        intents.guild_reactions = True
        intents.dm_messages = True
        intents.dm_reactions = True
        intents.moderation = True
        intents.integrations = True
        intents.members = True
        intents.bans = True
        intents.presences = True
        # intents.emojis_and_stickers = True
        intents.voice_states = True
        intents.message_content = True

        super().__init__(command_prefix='/', intents=intents)

        self.guild_main = self.get_guild(DISCORD_GUILD)

    async def setup_hook(self):
        # Load cogs dynamically
        await self.load_cogs()

    async def load_cogs(self):
        print('Loading cogs...')

        for path in Path('src/cogs').glob('*.py'):
            # Remove the '.py' from the file name
            cog = path.stem

            # Construct the cog's import path
            cog_import_path = f'src.cogs.{cog}'

            try:
                await self.load_extension(cog_import_path)
                print(f'Successfully loaded cog: {cog}')
            except Exception as e:
                print(f'Failed to load cog {cog}: {e}')
