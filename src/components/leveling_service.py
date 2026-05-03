from logging import Logger
from typing import Any, Mapping, Optional, Union
import discord
from motor.motor_asyncio import AsyncIOMotorClient
from src.helpers.env import MONGO_DATABASE
from src.helpers.config_keys import ConfigKey
from src.components.configuration_service import ConfigurationService
import time

MessageableChannel = Union[
    discord.TextChannel,
    discord.VoiceChannel,
    discord.StageChannel,
    discord.Thread,
    discord.DMChannel,
    discord.PartialMessageable,
    discord.GroupChannel,
]

class LevelingService:
    def __init__(self, db_client: AsyncIOMotorClient, logger: Logger, configuration_service: ConfigurationService):
        self.db = db_client.get_database(MONGO_DATABASE)
        self.collection = self.db.get_collection("leveling")
        self.logger = logger
        self.configuration_service = configuration_service
        self.xp_cooldown = 60  # seconds
        self._cooldowns = {}
        self._voice_activity = {}  # {guild_id: {user_id: count}}

    def get_xp_for_level(self, level: int) -> int:
        if level <= 0:
            return 0
        # Formula: sum_{i=0}^{level-1} (5*i^2 + 50*i + 100)
        # Using summation formulas:
        # sum_{i=0}^{n-1} i^2 = (n-1)n(2n-1)/6
        # sum_{i=0}^{n-1} i = (n-1)n/2
        # sum_{i=0}^{n-1} 1 = n
        n = level
        total_xp = (5 * (n - 1) * n * (2 * n - 1) // 6) + (50 * (n - 1) * n // 2) + (100 * n)
        return total_xp

    async def get_max_level(self, guild_id: int) -> int:
        return await self.configuration_service.get_config_value(guild_id, ConfigKey.LEVELING_MAX_LEVEL, 60)

    async def get_xp_per_message(self, guild_id: int) -> int:
        return await self.configuration_service.get_config_value(guild_id, ConfigKey.LEVELING_XP_PER_MESSAGE, 20)

    async def get_xp_per_voice_interval(self, guild_id: int) -> int:
        return await self.configuration_service.get_config_value(guild_id, ConfigKey.LEVELING_XP_PER_VOICE_INTERVAL, 5)

    async def get_voice_interval_minutes(self, guild_id: int) -> int:
        return await self.configuration_service.get_config_value(guild_id, ConfigKey.LEVELING_VOICE_INTERVAL_MINUTES, 15)

    async def get_level_from_xp(self, guild_id: int, xp: int) -> int:
        # Determine the level such that xp threshold (floored) is respected,
        # matching get_xp_for_level's integer truncation.
        if xp < 100:
            return 0
        # Binary search over levels 1..max_level for the highest level with threshold <= xp
        max_level = await self.get_max_level(guild_id)
        lo, hi = 1, max_level
        ans = 1
        while lo <= hi:
            mid = (lo + hi) // 2
            req = self.get_xp_for_level(mid)
            if req <= xp:
                ans = mid
                lo = mid + 1
            else:
                hi = mid - 1
        return ans

    async def initialize_user(self, guild_id: int, user_id: int):
        existing = await self.collection.find_one({"guild_id": guild_id, "user_id": user_id})
        if not existing:
            await self.collection.insert_one({
                "guild_id": guild_id,
                "user_id": user_id,
                "xp": 0,
                "level": 0,
                "last_xp_gain": 0
            })
            self.logger.info(f"Initialized leveling record for user {user_id} in guild {guild_id}")

    async def add_voice_xp(self, member: discord.Member) -> bool:
        guild_id = member.guild.id

        xp_amount = await self.get_xp_per_voice_interval(guild_id)
        
        # Check for excluded channels/categories
        if member.voice and member.voice.channel:
            channel = member.voice.channel
            excluded_channels = await self.get_excluded_channels(guild_id)

            if channel.id in excluded_channels:
                return False
            
            if hasattr(channel, "category_id") and channel.category_id:
                excluded_categories = await self.get_excluded_categories(guild_id)

                if channel.category_id in excluded_categories:
                    return False
        
        # Use add_xp but with a separate cooldown mechanism for voice if needed.
        return await self._add_xp_internal(member, member.voice.channel if member.voice else None, xp_amount, cooldown_key=f"voice_{member.id}")

    async def increment_voice_activity(self, member: discord.Member):
        guild_id = member.guild.id
        user_id = member.id

        if guild_id not in self._voice_activity:
            self._voice_activity[guild_id] = {}

        self._voice_activity[guild_id][user_id] = self._voice_activity[guild_id].get(user_id, 0) + 1

    async def get_voice_activity(self, guild_id: int, user_id: int) -> int:
        return self._voice_activity.get(guild_id, {}).get(user_id, 0)

    async def reset_voice_activity(self, guild_id: int):
        if guild_id in self._voice_activity:
            self._voice_activity[guild_id] = {}

    async def _add_xp_internal(self, member: discord.Member, channel: Optional[MessageableChannel] = None, xp_amount: int = 0, cooldown_key: Optional[str] = None) -> bool:
        user_id = member.id
        guild_id = member.guild.id

        current_time = time.time()

        xp_cooldown_key = cooldown_key or str(user_id)

        if xp_cooldown_key in self._cooldowns and current_time - self._cooldowns[xp_cooldown_key] < self.xp_cooldown:
            return False

        await self.initialize_user(guild_id, user_id)
        
        # Check if user already reached max level
        max_level = await self.get_max_level(guild_id)
        user_data = await self.get_user_data(guild_id, user_id)

        if user_data.get("level", 0) >= max_level:
            return False

        user_data = await self.collection.find_one_and_update(
            {"guild_id": guild_id, "user_id": user_id},
            {"$inc": {"xp": xp_amount}, "$set": {"last_xp_gain": current_time}},
            return_document=True
        )

        self._cooldowns[xp_cooldown_key] = current_time

        new_xp = user_data["xp"]
        old_level = user_data["level"]

        new_level = await self.get_level_from_xp(guild_id, new_xp)

        if new_level > old_level:
            await self.collection.update_one(
                {"guild_id": guild_id, "user_id": user_id},
                {"$set": {"level": new_level}}
            )

            await self._handle_level_up(member, new_level, channel)

            return True
        
        return False

    async def add_xp(self, member: discord.Member, channel: Optional[MessageableChannel] = None, xp_amount: Optional[int] = None) -> bool:
        guild_id = member.guild.id
        
        # Check for excluded channels/categories
        if channel:
            excluded_channels = await self.get_excluded_channels(guild_id)

            if channel.id in excluded_channels:
                return False

            if hasattr(channel, "category_id") and channel.category_id:
                excluded_categories = await self.get_excluded_categories(guild_id)

                if channel.category_id in excluded_categories:
                    return False

        if xp_amount is None:
            xp_amount = await self.get_xp_per_message(guild_id)

        return await self._add_xp_internal(member, channel, xp_amount)

    async def _handle_level_up(self, member: discord.Member, new_level: int, channel: Optional[MessageableChannel] = None):
        self.logger.info(f"User {member.id} leveled up to {new_level} in guild {member.guild.id}")

        leveling_roles = await self.configuration_service.get_config_value(member.guild.id, ConfigKey.LEVELING_ROLES, {})
        assigned_role = await self._assign_leveling_role(member, new_level, leveling_roles)

        if assigned_role:
            await self._cleanup_old_leveling_roles(member, new_level, leveling_roles)

        if channel:
            await self._send_level_up_message(member, new_level, channel, assigned_role)

    async def _assign_leveling_role(self, member: discord.Member, level: int, leveling_roles: dict) -> Optional[discord.Role]:
        # Ranks every 5th level: 5, 10, 15, ..., 60
        if level % 5 != 0:
            return None

        role_id = leveling_roles.get(str(level))

        if not role_id:
            return None

        role = member.guild.get_role(int(role_id))

        if not role:
            self.logger.warning(f"Role ID {role_id} for level {level} not found in guild {member.guild.id}")
            return None

        try:
            await member.add_roles(role, reason=f"Reached level {level}")
            self.logger.info(f"Assigned role {role.name} to {member.id} for level {level} in guild {member.guild.id}")
            return role
        except discord.Forbidden:
            self.logger.error(f"Failed to assign role {role.id} to {member.id} in guild {member.guild.id}: Forbidden")
            return None

    async def _cleanup_old_leveling_roles(self, member: discord.Member, current_level: int, leveling_roles: dict):
        if not leveling_roles:
            return

        roles_to_remove = []
        for lv, r_id in leveling_roles.items():
            if int(lv) < current_level:
                role = member.guild.get_role(int(r_id))
                if role and role in member.roles:
                    roles_to_remove.append(role)

        if roles_to_remove:
            try:
                await member.remove_roles(*roles_to_remove, reason=f"Leveled up to {current_level}")
                self.logger.info(f"Removed {len(roles_to_remove)} older leveling roles from {member.id} in guild {member.guild.id}:")
            except discord.Forbidden:
                self.logger.error(f"Failed to remove older leveling roles from {member.id} in guild {member.guild.id}: Forbidden")

    async def _send_level_up_message(self, member: discord.Member, level: int, channel: MessageableChannel, assigned_role: Optional[discord.Role]):
        message = f"Glückwunsch {member.mention}, du bist gerade auf Level {level} aufgestiegen!"
        if assigned_role:
            message += f" Du bist nun {assigned_role.name}!"

        try:
            await channel.send(message)
        except discord.Forbidden:
            self.logger.warning(f"Could not send level up message to channel {channel.id} in guild {member.guild.id}: Forbidden")

    async def get_user_data(self, guild_id: int, user_id: int) -> dict:
        data = await self.collection.find_one({"guild_id": guild_id, "user_id": user_id})
        if not data:
            return {"xp": 0, "level": 0}
        return data

    async def restore_level_roles(self, member: discord.Member):
        user_data = await self.get_user_data(member.guild.id, member.id)
        current_level = user_data.get("level", 0)

        leveling_roles = await self.configuration_service.get_config_value(member.guild.id, ConfigKey.LEVELING_ROLES, {})
        if not leveling_roles:
            return

        highest_lv = -1
        highest_role = None
        all_leveling_roles = []

        for lv_str, r_id in leveling_roles.items():
            lv = int(lv_str)
            role = member.guild.get_role(int(r_id))
            if not role:
                continue

            all_leveling_roles.append(role)
            if lv <= current_level and lv > highest_lv:
                highest_lv = lv
                highest_role = role

        roles_to_add = [highest_role] if highest_role and highest_role not in member.roles else []
        roles_to_remove = [r for r in all_leveling_roles if r != highest_role and r in member.roles]

        try:
            if roles_to_add:
                await member.add_roles(*roles_to_add, reason="Restoring leveling roles")
                self.logger.info(f"Restored role {highest_role.name} to {member.id} (level {current_level}) for guild {member.guild.id}")

            if roles_to_remove:
                await member.remove_roles(*roles_to_remove, reason="Cleaning up leveling roles")
                self.logger.info(f"Removed {len(roles_to_remove)} leveling roles from {member.id} for guild {member.guild.id}")
        except discord.Forbidden:
            self.logger.error(f"Failed to restore/cleanup leveling roles for {member.id} in guild {member.guild.id}: Forbidden")

    async def get_all_guild_users(self, guild_id: int) -> list[Mapping[str, Any]]:
        cursor = self.collection.find({"guild_id": guild_id})
        return await cursor.to_list(length=None)

    async def set_level_role(self, guild_id: int, level: int, role_id: int):
        max_level = await self.get_max_level(guild_id)
        if level % 5 != 0 or level < 5 or level > max_level:
            raise ValueError(f"Level must be a multiple of 5 between 5 and {max_level}")
        
        leveling_roles = await self.configuration_service.get_config_value(guild_id, ConfigKey.LEVELING_ROLES, {})
        leveling_roles[str(level)] = role_id
        await self.configuration_service.set_config_value(guild_id, ConfigKey.LEVELING_ROLES, leveling_roles)

    async def set_max_level(self, guild_id: int, max_level: int):
        if max_level < 1:
            raise ValueError("Maximum level must be at least 1")
        await self.configuration_service.set_config_value(guild_id, ConfigKey.LEVELING_MAX_LEVEL, max_level)

    async def set_xp_per_message(self, guild_id: int, xp_amount: int):
        if xp_amount < 1:
            raise ValueError("XP per message must be at least 1")
        await self.configuration_service.set_config_value(guild_id, ConfigKey.LEVELING_XP_PER_MESSAGE, xp_amount)

    async def set_xp_per_voice_interval(self, guild_id: int, xp_amount: int):
        if xp_amount < 1:
            raise ValueError("XP per voice interval must be at least 1")
        await self.configuration_service.set_config_value(guild_id, ConfigKey.LEVELING_XP_PER_VOICE_INTERVAL, xp_amount)

    async def set_voice_interval_minutes(self, guild_id: int, interval_minutes: int):
        if interval_minutes < 1:
            raise ValueError("Voice interval must be at least 1 minute")
        await self.configuration_service.set_config_value(guild_id, ConfigKey.LEVELING_VOICE_INTERVAL_MINUTES, interval_minutes)

    async def toggle_channel_exclusion(self, guild_id: int, channel_id: int) -> bool:
        excluded = await self.configuration_service.get_config_value(guild_id, ConfigKey.LEVELING_EXCLUDED_CHANNELS, [])
        if channel_id in excluded:
            excluded.remove(channel_id)
            is_excluded = False
        else:
            excluded.append(channel_id)
            is_excluded = True
        await self.configuration_service.set_config_value(guild_id, ConfigKey.LEVELING_EXCLUDED_CHANNELS, excluded)
        return is_excluded

    async def toggle_category_exclusion(self, guild_id: int, category_id: int) -> bool:
        excluded = await self.configuration_service.get_config_value(guild_id, ConfigKey.LEVELING_EXCLUDED_CATEGORIES, [])
        if category_id in excluded:
            excluded.remove(category_id)
            is_excluded = False
        else:
            excluded.append(category_id)
            is_excluded = True
        await self.configuration_service.set_config_value(guild_id, ConfigKey.LEVELING_EXCLUDED_CATEGORIES, excluded)
        return is_excluded

    async def get_excluded_channels(self, guild_id: int) -> list[int]:
        return await self.configuration_service.get_config_value(guild_id, ConfigKey.LEVELING_EXCLUDED_CHANNELS, [])

    async def get_excluded_categories(self, guild_id: int) -> list[int]:
        return await self.configuration_service.get_config_value(guild_id, ConfigKey.LEVELING_EXCLUDED_CATEGORIES, [])
