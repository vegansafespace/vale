import discord
from discord import app_commands
from discord.ext import commands
from logging import Logger
from dependency_injector.wiring import inject
from src.components.configuration_service import ConfigurationService
from src.main import container
from src.vale import Vale
from src.helpers.env import TEAM_ROLE_ID
from src.helpers.config_keys import ConfigKey


class ConfigUtils(commands.Cog):
    @inject
    def __init__(self, logger: Logger, bot: Vale, configuration_service: ConfigurationService):
        self.logger = logger
        self.bot = bot
        self.configuration_service = configuration_service

    config_group = app_commands.Group(name="config", description="Manage bot configuration")
    set_group = app_commands.Group(name="set", description="Set configuration values", parent=config_group)

    async def _set_category_id(self, interaction: discord.Interaction, key: ConfigKey, name: str):
        channel = interaction.channel

        if channel is None:
            await interaction.response.send_message(f"No channel found for this interaction.", ephemeral=True)
            return

        category = interaction.channel.category

        if category is None:
            await interaction.response.send_message(f"Please move this channel to a category first.", ephemeral=True)
            return

        await self.configuration_service.set_config_value(interaction.guild_id, key, category.id)
        await interaction.response.send_message(f"{name} ID set to {category.id} ({category.name})", ephemeral=True)

    async def _set_channel_id(self, interaction: discord.Interaction, key: ConfigKey, name: str):
        channel_id = interaction.channel_id
        await self.configuration_service.set_config_value(interaction.guild_id, key, channel_id)
        await interaction.response.send_message(f"{name} ID set to {channel_id} (current channel)", ephemeral=True)

    @set_group.command(
        name="application-category",
        description="Set the category ID for application channels to the current category"
    )
    @app_commands.guild_only()
    @app_commands.checks.has_role(TEAM_ROLE_ID)
    async def set_application_category_id(self, interaction: discord.Interaction):
        await self._set_category_id(interaction, ConfigKey.APPLICATION_CATEGORY_ID, "Application category")

    @set_group.command(
        name="private-channels-category",
        description="Set the category ID for private channels to the current category"
    )
    @app_commands.guild_only()
    @app_commands.checks.has_role(TEAM_ROLE_ID)
    async def set_private_channels_category_id(self, interaction: discord.Interaction):
        await self._set_category_id(interaction, ConfigKey.PRIVATE_CHANNELS_CATEGORY_ID, "Private channels category")

    @set_group.command(
        name="voice-hub-category",
        description="Set the category ID for voice hub channels to the current category"
    )
    @app_commands.guild_only()
    @app_commands.checks.has_role(TEAM_ROLE_ID)
    async def set_voice_hub_category_id(self, interaction: discord.Interaction):
        await self._set_category_id(interaction, ConfigKey.VOICE_HUB_CATEGORY_ID, "Voice hub category")

    @set_group.command(
        name="voice-category",
        description="Set the category ID for voice channels to the current category"
    )
    @app_commands.guild_only()
    @app_commands.checks.has_role(TEAM_ROLE_ID)
    async def set_voice_category_id(self, interaction: discord.Interaction):
        await self._set_category_id(interaction, ConfigKey.VOICE_CATEGORY_ID, "Voice category")

    @set_group.command(
        name="application-voice-waiting-channel",
        description="Set the application voice waiting channel ID to the current channel"
    )
    @app_commands.guild_only()
    @app_commands.checks.has_role(TEAM_ROLE_ID)
    async def set_application_voice_waiting_channel_id(self, interaction: discord.Interaction):
        await self._set_channel_id(interaction, ConfigKey.APPLICATION_VOICE_WAITING_CHANNEL_ID, "Application voice waiting channel")

    @set_group.command(
        name="voice-hub-move-me-channel",
        description="Set the voice hub move me channel ID to the current channel"
    )
    @app_commands.guild_only()
    @app_commands.checks.has_role(TEAM_ROLE_ID)
    async def set_voice_hub_move_me_channel_id(self, interaction: discord.Interaction):
        await self._set_channel_id(interaction, ConfigKey.VOICE_HUB_MOVE_ME_CHANNEL_ID, "Voice hub move me channel")

    @set_group.command(
        name="voice-hub-create-channel",
        description="Set the voice hub create channel ID to the current channel"
    )
    @app_commands.guild_only()
    @app_commands.checks.has_role(TEAM_ROLE_ID)
    async def set_voice_hub_create_channel_id(self, interaction: discord.Interaction):
        await self._set_channel_id(interaction, ConfigKey.VOICE_HUB_CREATE_CHANNEL_ID, "Voice hub create channel")

    @set_group.command(
        name="application-ping-channel",
        description="Set the application ping channel ID to the current channel"
    )
    @app_commands.guild_only()
    @app_commands.checks.has_role(TEAM_ROLE_ID)
    async def set_application_ping_channel_id(self, interaction: discord.Interaction):
        await self._set_channel_id(interaction, ConfigKey.APPLICATION_PING_CHANNEL_ID, "Application ping channel")

    @set_group.command(
        name="reports-channel",
        description="Set the reports channel ID to the current channel"
    )
    @app_commands.guild_only()
    @app_commands.checks.has_role(TEAM_ROLE_ID)
    async def set_reports_channel_id(self, interaction: discord.Interaction):
        await self._set_channel_id(interaction, ConfigKey.REPORTS_CHANNEL_ID, "Reports channel")

    @set_group.command(
        name="role-justification-channel",
        description="Set the role justification channel ID to the current channel"
    )
    @app_commands.guild_only()
    @app_commands.checks.has_role(TEAM_ROLE_ID)
    async def set_role_justification_channel_id(self, interaction: discord.Interaction):
        await self._set_channel_id(interaction, ConfigKey.ROLE_JUSTIFICATION_CHANNEL_ID, "Role justification channel")

    @set_group.command(
        name="team-bans-channel",
        description="Set the team bans channel ID to the current channel"
    )
    @app_commands.guild_only()
    @app_commands.checks.has_role(TEAM_ROLE_ID)
    async def set_team_bans_channel_id(self, interaction: discord.Interaction):
        await self._set_channel_id(interaction, ConfigKey.TEAM_BANS_CHANNEL_ID, "Team bans channel")

    @set_group.command(
        name="team-applications-channel",
        description="Set the team applications channel ID to the current channel"
    )
    @app_commands.guild_only()
    @app_commands.checks.has_role(TEAM_ROLE_ID)
    async def set_team_applications_channel_id(self, interaction: discord.Interaction):
        await self._set_channel_id(interaction, ConfigKey.TEAM_APPLICATIONS_CHANNEL_ID, "Team applications channel")

    @set_group.command(
        name="main-chat-channel",
        description="Set the main chat channel ID to the current channel"
    )
    @app_commands.guild_only()
    @app_commands.checks.has_role(TEAM_ROLE_ID)
    async def set_main_chat_channel_id(self, interaction: discord.Interaction):
        await self._set_channel_id(interaction, ConfigKey.MAIN_CHAT_CHANNEL_ID, "Main chat channel")

    @set_group.command(
        name="non-vegan-main-chat-channel",
        description="Set the non-vegan main chat channel ID to the current channel"
    )
    @app_commands.guild_only()
    @app_commands.checks.has_role(TEAM_ROLE_ID)
    async def set_non_vegan_main_chat_channel_id(self, interaction: discord.Interaction):
        await self._set_channel_id(interaction, ConfigKey.NON_VEGAN_MAIN_CHAT_CHANNEL_ID, "Non-vegan main chat channel")

async def setup(bot: Vale):
    await bot.add_cog(
        ConfigUtils(
            logger=container.logger(),
            bot=bot,
            configuration_service=container.configuration_service(),
        )
    )
