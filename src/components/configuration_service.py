from logging import Logger
from typing import Any, Dict, Union
from motor.motor_asyncio import AsyncIOMotorClient
from src.helpers.env import MONGO_DATABASE
from src.helpers.config_keys import ConfigKey

class ConfigurationService:
    def __init__(self, db_client: AsyncIOMotorClient, logger: Logger):
        self.db = db_client.get_database(MONGO_DATABASE)
        self.collection = self.db.get_collection("configurations")
        self.logger = logger
        self._cache: Dict[int, Dict[str, Any]] = {}

    async def get_config(self, guild_id: int) -> dict:
        if guild_id in self._cache:
            return self._cache[guild_id]

        config = await self.collection.find_one({"guild_id": guild_id})
        settings = config.get("settings", {}) if config else {}

        self._cache[guild_id] = settings

        return settings

    async def set_config_value(self, guild_id: int, key: Union[ConfigKey, str], value: Any):
        key_str = key.value if isinstance(key, ConfigKey) else key

        await self.collection.update_one(
            {"guild_id": guild_id},
            {"$set": {f"settings.{key_str}": value}},
            upsert=True
        )

        # Update cache
        if guild_id not in self._cache:
            self._cache[guild_id] = {}

        self._cache[guild_id][key_str] = value

        self.logger.info(f"Set config {key_str}={value} for guild {guild_id}")

    async def get_config_value(self, guild_id: int, key: Union[ConfigKey, str], default: Any = None) -> Any:
        key_str = key.value if isinstance(key, ConfigKey) else key
        config = await self.get_config(guild_id)

        return config.get(key_str, default)
