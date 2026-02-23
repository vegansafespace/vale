from logging import Logger

import discord
from dependency_injector.wiring import inject
from discord.ext import commands

from src.components.application import Application
from src.components.application_service import ApplicationService
from src.components.voice_category import VoiceCategory
from src.components.voice_hub import VoiceHub
from src.helpers.env import NEW_USER_ROLE_ID, VOICE_HUB_MOVE_ME_CHANNEL_ID, VOICE_HUB_CREATE_CHANNEL_ID, \
    APPLICATION_VOICE_WAITING_CHANNEL_ID, VOICE_CATEGORY_ID, VOICE_HUB_CATEGORY_ID, APPLICATION_CATEGORY_ID
from src.helpers.config_keys import ConfigKey
from src.components.configuration_service import ConfigurationService
from src.main import container
from src.vale import Vale


class Events(commands.Cog):
    @inject
    def __init__(self, logger: Logger, bot: Vale, application: Application, application_service: ApplicationService, voice_category: VoiceCategory, voice_hub: VoiceHub, configuration_service: ConfigurationService):
        self.bot = bot

        self.logger = logger
        self.application = application
        self.application_service = application_service
        self.voice_category = voice_category
        self.voice_hub = voice_hub
        self.configuration_service = configuration_service

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        self.logger.info(f'{member} (ID: {member.id}) joined the server!')

        new_user_role = discord.utils.get(member.guild.roles, id=NEW_USER_ROLE_ID)

        if new_user_role is None:
            return

        await member.add_roles(new_user_role)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        self.logger.info(f'{member} (ID: {member.id}) left the server!')

        await self.application_service.revoke_application(
            member.guild,
            member,
            reason="Die Person hat den Server verlassen."
        )

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState,
                                    after: discord.VoiceState):
        # Check if joined or left channel
        if before.channel == after.channel:
            return

        # Check if user joined the move-me channel
        voice_hub_move_me_channel_id = await self.configuration_service.get_config_value(member.guild.id, ConfigKey.VOICE_HUB_MOVE_ME_CHANNEL_ID, VOICE_HUB_MOVE_ME_CHANNEL_ID)
        if after.channel is not None and after.channel.id == voice_hub_move_me_channel_id:
            await self.voice_hub.on_join_move_me_channel(member, before, after)

        # Check if user joined the create channel
        voice_hub_create_channel_id = await self.configuration_service.get_config_value(member.guild.id, ConfigKey.VOICE_HUB_CREATE_CHANNEL_ID, VOICE_HUB_CREATE_CHANNEL_ID)
        if after.channel is not None and after.channel.id == voice_hub_create_channel_id:
            await self.voice_hub.on_join_create_channel(member, before, after)

        # Check if user joined the application waiting room
        application_voice_waiting_channel_id = await self.configuration_service.get_config_value(member.guild.id, ConfigKey.APPLICATION_VOICE_WAITING_CHANNEL_ID, APPLICATION_VOICE_WAITING_CHANNEL_ID)
        if after.channel is not None and after.channel.id == application_voice_waiting_channel_id:
            await self.application.on_join_waiting_room(member, before, after)

        # Check if user joined any of the voice channels in the voice category
        voice_category_id = await self.configuration_service.get_config_value(member.guild.id, ConfigKey.VOICE_CATEGORY_ID, VOICE_CATEGORY_ID)
        if after.channel is not None and after.channel.category_id == voice_category_id:
            await self.voice_category.on_join(member, before, after, self.bot)

        # Check if user left any of the voice channels in the voice category
        if before.channel is not None and before.channel.category_id == voice_category_id:
            await self.voice_category.on_leave(member, before, after, self.bot)

        # Check if user left the application waiting room
        if before.channel is not None and before.channel.id == application_voice_waiting_channel_id:
            await self.application.on_leave_waiting_room(member, before, after)

        # Check if user left the move me channel
        if before.channel is not None and before.channel.id == voice_hub_move_me_channel_id:
            await self.voice_hub.on_leave_move_me_channel(member, before, after)

        # Check if user left a voice hub channel
        voice_hub_category_id = await self.configuration_service.get_config_value(member.guild.id, ConfigKey.VOICE_HUB_CATEGORY_ID, VOICE_HUB_CATEGORY_ID)
        if before.channel is not None and before.channel.category_id == voice_hub_category_id:
            await self.voice_hub.on_leave_hub_channel(member, before, after)

        # Check if user left an application voice channel
        application_category_id = await self.configuration_service.get_config_value(member.guild.id, ConfigKey.APPLICATION_CATEGORY_ID, APPLICATION_CATEGORY_ID)
        if before.channel is not None and before.channel.category_id == application_category_id:
            await self.application.on_leave_application_voice(member, before, after)


async def setup(bot: Vale):
    await bot.add_cog(
        Events(
            logger=container.logger(),
            bot=bot,
            application=container.application(),
            application_service=container.application_service(),
            voice_category=container.voice_category(),
            voice_hub=container.voice_hub(),
            configuration_service=container.configuration_service(),
        )
    )
