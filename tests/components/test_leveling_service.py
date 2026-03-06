import pytest
import math
import discord
from src.components.leveling_service import LevelingService
from src.helpers.config_keys import ConfigKey
from unittest.mock import MagicMock, AsyncMock

@pytest.fixture
def leveling_service():
    # We only need it for the math functions, so we can mock the dependencies
    cfg = MagicMock()
    cfg.get_config_value = AsyncMock(return_value=60)
    return LevelingService(db_client=MagicMock(), logger=MagicMock(), configuration_service=cfg)

def test_get_xp_for_level(leveling_service):
    # Level 0 should be 0 XP
    assert leveling_service.get_xp_for_level(0) == 0
    assert leveling_service.get_xp_for_level(-1) == 0
    
    assert leveling_service.get_xp_for_level(1) == 100
    assert leveling_service.get_xp_for_level(2) == 255
    assert leveling_service.get_xp_for_level(3) == 475
    assert leveling_service.get_xp_for_level(5) == 1150
    assert leveling_service.get_xp_for_level(10) == 4675
    assert leveling_service.get_xp_for_level(15) == 11825
    assert leveling_service.get_xp_for_level(30) == 67525
    assert leveling_service.get_xp_for_level(60) == 445550
    assert leveling_service.get_xp_for_level(80) == 1003400
    assert leveling_service.get_xp_for_level(90) == 1404075
    assert leveling_service.get_xp_for_level(100) == 1899250

@pytest.mark.asyncio
async def test_get_level_from_xp(leveling_service):
    # XP < 100 should be level 0
    assert await leveling_service.get_level_from_xp(1, 0) == 0
    assert await leveling_service.get_level_from_xp(1, 99) == 0
    
    # XP 100 to 254 should be level 1
    assert await leveling_service.get_level_from_xp(1, 100) == 1
    assert await leveling_service.get_level_from_xp(1, 254) == 1
    
    # XP 255 should be level 2
    assert await leveling_service.get_level_from_xp(1, 255) == 2

    # XP 445550 should be level 60
    assert await leveling_service.get_level_from_xp(1, 445550) == 60

    # XP 835375 should be level 60 (capped to 60 per default)
    assert await leveling_service.get_level_from_xp(1, 835375) == 60

    # XP 1899250 should be level 60 (capped to 60 per default)
    assert await leveling_service.get_level_from_xp(1, 1899250) == 60

    # Mock get_max_level to return 60
    leveling_service.get_max_level = MagicMock(return_value=60)
    # Since it's an async function being called with await, we need it to return a future/coroutine
    async def mock_get_max_level(guild_id):
        return 60
    leveling_service.get_max_level = mock_get_max_level

    # Boundary checks around several levels using the floored thresholds
    for level in [3, 5, 10, 20, 60]:
        threshold = leveling_service.get_xp_for_level(level)
        assert await leveling_service.get_level_from_xp(1, threshold - 1) == max(0, level - 1)
        assert await leveling_service.get_level_from_xp(1, threshold) == level
    
    # Test level 60: upper bound and capping
    assert await leveling_service.get_level_from_xp(1, 445550) == 60
    assert await leveling_service.get_level_from_xp(1, 1000000) == 60 # Capped at 60

    # Test with different max level
    async def mock_get_max_level_100(guild_id):
        return 100
    leveling_service.get_max_level = mock_get_max_level_100
    assert await leveling_service.get_level_from_xp(1, 1899250) == 100
    assert await leveling_service.get_level_from_xp(1, 1899250 + 1000) == 100

@pytest.mark.asyncio
async def test_consistency(leveling_service):
    # Mock get_max_level to return 100
    async def mock_get_max_level(guild_id):
        return 100
    leveling_service.get_max_level = mock_get_max_level

    # Test that get_level_from_xp(get_xp_for_level(L)) == L for L in 1..100
    for l in range(1, 101):
        xp = leveling_service.get_xp_for_level(l)
        calc_l = await leveling_service.get_level_from_xp(1, xp)
        assert calc_l == l, f"Failed at level {l}: XP={xp}, calc_level={calc_l}"

@pytest.mark.asyncio
async def test_add_xp_max_level(leveling_service):
    # Mock dependencies for add_xp
    guild_id = 1
    user_id = 123
    member = MagicMock()
    member.id = user_id
    member.guild.id = guild_id
    
    # Mock database collection
    leveling_service.collection = AsyncMock()
    
    # Mock get_max_level to return 5
    leveling_service.get_max_level = AsyncMock(return_value=5)
    
    # Case 1: User is at level 4, should gain XP
    leveling_service.get_xp_per_message = AsyncMock(return_value=20)
    leveling_service.collection.find_one = AsyncMock(return_value={"level": 4, "xp": 100})
    leveling_service.collection.find_one_and_update = AsyncMock(return_value={"level": 4, "xp": 120})
    leveling_service.get_level_from_xp = AsyncMock(return_value=4)
    
    result = await leveling_service.add_xp(member, None)
    assert result is False # No level up, but XP was added (find_one_and_update called)
    assert leveling_service.collection.find_one_and_update.called
    
    # Case 1.5: User gains specific XP amount
    mock_update = AsyncMock(return_value={"level": 4, "xp": 135})
    leveling_service.collection.find_one_and_update = mock_update
    leveling_service._cooldowns = {} # Clear cooldowns
    await leveling_service.add_xp(member, None, xp_amount=25)
    # Check that $inc was called with 25
    assert mock_update.call_count == 1
    args, kwargs = mock_update.call_args_list[0]
    assert args[1]["$inc"]["xp"] == 25

    # Case 2: User is at level 5 (max), should NOT gain XP
    leveling_service.collection.find_one_and_update.reset_mock()
    leveling_service.collection.find_one = AsyncMock(return_value={"level": 5, "xp": 146})
    
    result = await leveling_service.add_xp(member, None, 10)
    assert result is False
    assert not leveling_service.collection.find_one_and_update.called

@pytest.mark.asyncio
async def test_add_xp_excluded_channel(leveling_service):
    guild_id = 1
    user_id = 123
    member = MagicMock()
    member.id = user_id
    member.guild.id = guild_id
    
    channel = MagicMock(spec=discord.TextChannel)
    channel.id = 111
    channel.category_id = 222
    
    leveling_service.configuration_service.get_config_value = AsyncMock()
    
    # Mock find_one_and_update to see if it's called
    leveling_service.collection = AsyncMock()

    # Case 1: Channel is excluded
    async def side_effect(gid, key, default):
        if key == ConfigKey.LEVELING_EXCLUDED_CHANNELS:
            return [111]
        return default
    leveling_service.configuration_service.get_config_value.side_effect = side_effect
    
    result = await leveling_service.add_xp(member, channel)
    assert result is False
    assert not leveling_service.collection.find_one_and_update.called

    # Case 2: Category is excluded
    async def side_effect_cat(gid, key, default):
        if key == ConfigKey.LEVELING_EXCLUDED_CHANNELS:
            return []
        if key == ConfigKey.LEVELING_EXCLUDED_CATEGORIES:
            return [222]
        return default
    leveling_service.configuration_service.get_config_value.side_effect = side_effect_cat
    
    result = await leveling_service.add_xp(member, channel)
    assert result is False
    assert not leveling_service.collection.find_one_and_update.called

    # Case 3: Not excluded
    async def side_effect_none(gid, key, default):
        return default
    leveling_service.configuration_service.get_config_value.side_effect = side_effect_none
    leveling_service.get_max_level = AsyncMock(return_value=60)
    leveling_service.get_user_data = AsyncMock(return_value={"level": 0, "xp": 0})
    leveling_service.get_xp_per_message = AsyncMock(return_value=20)
    leveling_service.collection.find_one_and_update = AsyncMock(return_value={"level": 0, "xp": 20})
    leveling_service.get_level_from_xp = AsyncMock(return_value=0)
    
    result = await leveling_service.add_xp(member, channel)
    # XP added, but no level up, so returns False. But find_one_and_update should be called.
    assert result is False
    assert leveling_service.collection.find_one_and_update.called

@pytest.mark.asyncio
async def test_level_up_notification(leveling_service):
    guild_id = 1
    user_id = 123
    member = MagicMock()
    member.id = user_id
    member.guild.id = guild_id
    member.mention = "<@123>"
    member.add_roles = AsyncMock()
    
    channel = AsyncMock()
    
    leveling_service.collection = AsyncMock()
    leveling_service.get_xp_per_message = AsyncMock(return_value=20)
    leveling_service.get_max_level = AsyncMock(return_value=60)
    leveling_service.get_user_data = AsyncMock(return_value={"level": 4, "xp": 150})
    leveling_service.collection.find_one_and_update = AsyncMock(return_value={"level": 4, "xp": 170})
    leveling_service.get_level_from_xp = AsyncMock(return_value=5)
    
    # Mock configuration for role
    leveling_service.configuration_service.get_config_value = AsyncMock(return_value={"5": 999})
    role = MagicMock()
    role.name = "Test Role"
    member.guild.get_role = MagicMock(return_value=role)
    
    result = await leveling_service.add_xp(member, channel)
    
    assert result is True
    channel.send.assert_called_with("Glückwunsch <@123>, du bist gerade auf Level 5 aufgestiegen! Du bist nun Test Role!")

@pytest.mark.asyncio
async def test_role_retention_on_intermediate_level_up(leveling_service):
    guild_id = 1
    user_id = 123
    member = MagicMock()
    member.id = user_id
    member.guild.id = guild_id
    member.roles = [] # Start with no roles
    member.add_roles = AsyncMock()
    
    # Mock role for level 5
    role_lv5 = MagicMock()
    role_lv5.id = 555
    role_lv5.name = "Level 5 Role"
    member.guild.get_role = MagicMock(side_effect=lambda rid: role_lv5 if rid == 555 else None)
    
    leveling_service.collection = AsyncMock()
    leveling_service.get_max_level = AsyncMock(return_value=60)
    leveling_service.configuration_service.get_config_value = AsyncMock(return_value={"5": 555})
    
    # 1. Level up from 4 to 5 (Should assign role)
    leveling_service.get_user_data = AsyncMock(return_value={"level": 4, "xp": leveling_service.get_xp_for_level(5) - 10})
    leveling_service.collection.find_one_and_update = AsyncMock(return_value={"level": 4, "xp": leveling_service.get_xp_for_level(5)})
    leveling_service.get_level_from_xp = AsyncMock(return_value=5)
    
    channel = AsyncMock()
    await leveling_service.add_xp(member, channel)
    
    member.add_roles.assert_called_with(role_lv5, reason="Reached level 5")
    member.roles.append(role_lv5) # Simulate role addition
    
    # 2. Level up from 5 to 6 (Should NOT remove level 5 role, because no new role is assigned at level 6)
    member.add_roles.reset_mock()
    member.remove_roles = AsyncMock()
    
    leveling_service.get_user_data = AsyncMock(return_value={"level": 5, "xp": leveling_service.get_xp_for_level(6) - 10})
    leveling_service.collection.find_one_and_update = AsyncMock(return_value={"level": 5, "xp": leveling_service.get_xp_for_level(6)})
    leveling_service.get_level_from_xp = AsyncMock(return_value=6)
    
    # Clear cooldown to allow immediate XP gain
    leveling_service._cooldowns = {}
    
    await leveling_service.add_xp(member, channel)
    
    # No new role at level 6
    member.add_roles.assert_not_called()
    # Level 5 role should still be there, so remove_roles should NOT be called
    member.remove_roles.assert_not_called()

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
