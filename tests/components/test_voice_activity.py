import pytest
from unittest.mock import MagicMock, AsyncMock
import discord
from src.components.leveling_service import LevelingService

@pytest.fixture
def leveling_service():
    cfg = MagicMock()
    cfg.get_config_value = AsyncMock(return_value=60)
    return LevelingService(db_client=MagicMock(), logger=MagicMock(), configuration_service=cfg)

@pytest.mark.asyncio
async def test_voice_activity_tracking(leveling_service):
    guild_id = 123
    member = MagicMock(spec=discord.Member)
    member.guild.id = guild_id
    member.id = 456
    
    # Test initial state
    assert await leveling_service.get_voice_activity(guild_id, member.id) == 0
    
    # Test increment
    await leveling_service.increment_voice_activity(member)
    assert await leveling_service.get_voice_activity(guild_id, member.id) == 1
    
    await leveling_service.increment_voice_activity(member)
    assert await leveling_service.get_voice_activity(guild_id, member.id) == 2
    
    # Test reset
    await leveling_service.reset_voice_activity(guild_id)
    assert await leveling_service.get_voice_activity(guild_id, member.id) == 0

@pytest.mark.asyncio
async def test_voice_activity_multi_user(leveling_service):
    guild_id = 123
    member1 = MagicMock(spec=discord.Member)
    member1.guild.id = guild_id
    member1.id = 1
    
    member2 = MagicMock(spec=discord.Member)
    member2.guild.id = guild_id
    member2.id = 2
    
    await leveling_service.increment_voice_activity(member1)
    await leveling_service.increment_voice_activity(member2)
    await leveling_service.increment_voice_activity(member2)
    
    assert await leveling_service.get_voice_activity(guild_id, 1) == 1
    assert await leveling_service.get_voice_activity(guild_id, 2) == 2
    
    # Test reset only resets one guild (if we had multiple)
    guild_id_2 = 456
    member3 = MagicMock(spec=discord.Member)
    member3.guild.id = guild_id_2
    member3.id = 3
    
    await leveling_service.increment_voice_activity(member3)
    assert await leveling_service.get_voice_activity(guild_id_2, 3) == 1
    
    await leveling_service.reset_voice_activity(guild_id)
    assert await leveling_service.get_voice_activity(guild_id, 1) == 0
    assert await leveling_service.get_voice_activity(guild_id_2, 3) == 1
