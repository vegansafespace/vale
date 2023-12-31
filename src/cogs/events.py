import discord
from dependency_injector.wiring import inject
from discord.ext import commands

from src.components.application import Application
from src.components.voice_category import VoiceCategory
from src.components.voice_hub import VoiceHub
from src.helpers.env import NEW_USER_ROLE_ID, VOICE_HUB_MOVE_ME_CHANNEL_ID, VOICE_HUB_CREATE_CHANNEL_ID, \
    APPLICATION_VOICE_WAITING_CHANNEL_ID, VOICE_CATEGORY_ID, VOICE_HUB_CATEGORY_ID, VOICE_HUB_CHANNEL_PREFIX
from src.main import container
from src.vale import Vale


class Events(commands.Cog):
    @inject
    def __init__(self, bot: Vale, application: Application, voice_category: VoiceCategory, voice_hub: VoiceHub):
        self.bot = bot

        self.application = application
        self.voice_category = voice_category
        self.voice_hub = voice_hub

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        print(f'{member} (ID: {member.id}) joined the server!')
        new_user_role = discord.utils.get(member.guild.roles, id=NEW_USER_ROLE_ID)
        await member.add_roles(new_user_role)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState,
                                    after: discord.VoiceState):
        # Check if joined or left channel
        if before.channel == after.channel:
            return

        # Check if user joined the move-me channel
        if after.channel is not None and after.channel.id == VOICE_HUB_MOVE_ME_CHANNEL_ID:
            await self.voice_hub.on_join_move_me_channel(member, before, after)

        # Check if user joined the create channel
        if after.channel is not None and after.channel.id == VOICE_HUB_CREATE_CHANNEL_ID:
            await self.voice_hub.on_join_create_channel(member, before, after)

        # Check if user joined the application waiting room
        if after.channel is not None and after.channel.id == APPLICATION_VOICE_WAITING_CHANNEL_ID:
            await self.application.on_join_waiting_room(member, before, after)

        # Check if user joined any of the voice channels in the voice category
        if after.channel is not None and after.channel.category.id == VOICE_CATEGORY_ID:
            await self.voice_category.on_join(member, before, after)

        # Check if user left any of the voice channels in the voice category
        if before.channel is not None and before.channel.category.id == VOICE_CATEGORY_ID:
            await self.voice_category.on_leave(member, before, after)

        # Check if user left the application waiting room
        if before.channel is not None and before.channel.id == APPLICATION_VOICE_WAITING_CHANNEL_ID:
            await self.application.on_leave_waiting_room(member, before, after)

        # Check if user left a voice hub channel
        if before.channel is not None and before.channel.category_id == VOICE_HUB_CATEGORY_ID:
            # Check if is voice hub voice channel with VOICE_HUB_CHANNEL_PREFIX
            if before.channel.name.startswith(VOICE_HUB_CHANNEL_PREFIX):
                # Check if user is the only one left in the channel
                if len(before.channel.members) == 0:
                    # Delete channel
                    await before.channel.delete()


async def setup(bot: Vale):
    await bot.add_cog(
        Events(
            bot,
            application=container.application(),
            voice_category=container.voice_category(),
            voice_hub=container.voice_hub(),
        )
    )
