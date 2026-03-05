from logging import Logger
from pathlib import Path

import discord
from discord.ext import commands
from views.application_view import ApplicationView


class Vale(commands.Bot):
    def __init__(self, logger: Logger):
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

        super().__init__(command_prefix='!', intents=intents)

        self.logger = logger

    async def on_ready(self):
        guild_count = len(self.guilds)

        self.logger.info(
            f"Logged in as {self.user} (ID: {self.user.id}) in {guild_count} {'guild' if guild_count == 1 else 'guilds'}"
        )

    async def setup_hook(self):
        # Load cogs dynamically
        await self.load_cogs()

        # Add persistent views
        from src.main import container
        self.add_view(ApplicationView(application_service=container.application_service()))

    async def load_cogs(self):
        self.logger.info('Loading cogs...')

        for path in Path('src/cogs').glob('*.py'):
            # Remove the '.py' from the file name
            cog = path.stem

            # Construct the cog's import path
            cog_import_path = f'src.cogs.{cog}'

            try:
                await self.load_extension(cog_import_path)
                self.logger.info(f'Successfully loaded cog: {cog}')
            except Exception as e:
                self.logger.error(f'Failed to load cog {cog}: {e}')
