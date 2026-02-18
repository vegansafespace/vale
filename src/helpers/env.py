import os

from dotenv import load_dotenv

load_dotenv()

def get_env_var(name: str, default: str = None) -> str:
    value = os.getenv(name, default)
    if value:
        # Strip literal quotes that might be passed via environment
        return value.strip('"').strip("'")
    return value


DEBUG: bool = get_env_var('DEBUG', 'false').lower() == 'true'

MONGO_USERNAME: str = get_env_var('MONGO_USERNAME')
MONGO_PASSWORD: str = get_env_var('MONGO_PASSWORD')
MONGO_DATABASE: str = get_env_var('MONGO_DATABASE', 'vale')
MONGO_HOST: str = get_env_var('MONGO_HOST', 'localhost')
MONGO_PORT: int = int(get_env_var('MONGO_PORT', 27017))

DISCORD_TOKEN: str = get_env_var('DISCORD_TOKEN')
DISCORD_GUILD: int = int(get_env_var('DISCORD_GUILD'))

APPLICATION_CATEGORY_ID: int = int(get_env_var('APPLICATION_CATEGORY_ID'))
APPLICATION_VOICE_WAITING_CHANNEL_ID: int = int(get_env_var('APPLICATION_VOICE_WAITING_CHANNEL_ID'))
APPLICATION_PING_CHANNEL_ID: int = int(get_env_var('APPLICATION_PING_CHANNEL_ID'))

REPORTS_CHANNEL_ID: int = int(get_env_var('REPORTS_CHANNEL_ID'))
ROLE_JUSTIFICATION_CHANNEL_ID: int = int(get_env_var('ROLE_JUSTIFICATION_CHANNEL_ID'))

PRIVATE_CHANNELS_CATEGORY_ID: int = int(get_env_var('PRIVATE_CHANNELS_CATEGORY_ID'))

VOICE_HUB_CATEGORY_ID: int = int(get_env_var('VOICE_HUB_CATEGORY_ID'))
VOICE_HUB_MOVE_ME_CHANNEL_ID: int = int(get_env_var('VOICE_HUB_MOVE_ME_CHANNEL_ID'))
VOICE_HUB_CREATE_CHANNEL_ID: int = int(get_env_var('VOICE_HUB_CREATE_CHANNEL_ID'))
VOICE_HUB_CHANNEL_PREFIX: str = get_env_var('VOICE_HUB_CHANNEL_PREFIX')

VOICE_CATEGORY_ID: int = int(get_env_var('VOICE_CATEGORY_ID'))

TEAM_ROLE_ID: int = int(get_env_var('TEAM_ROLE_ID'))
NEW_USER_ROLE_ID: int = int(get_env_var('NEW_USER_ROLE_ID'))
SUPPORT_ROLE_ID: int = int(get_env_var('SUPPORT_ROLE_ID'))
VEGAN_ROLE_ID: int = int(get_env_var('VEGAN_ROLE_ID'))
NON_VEGAN_ROLE_ID: int = int(get_env_var('NON_VEGAN_ROLE_ID'))
OUTREACH_ROLE_ID: int = int(get_env_var('OUTREACH_ROLE_ID'))

TEAM_BANS_CHANNEL_ID: int = int(get_env_var('TEAM_BANS_CHANNEL_ID'))
TEAM_APPLICATIONS_CHANNEL_ID: int = int(get_env_var('TEAM_APPLICATIONS_CHANNEL_ID'))

MAIN_CHAT_CHANNEL_ID: int = int(get_env_var('MAIN_CHAT_CHANNEL_ID'))
NON_VEGAN_MAIN_CHAT_CHANNEL_ID: int = int(get_env_var('NON_VEGAN_MAIN_CHAT_CHANNEL_ID'))
