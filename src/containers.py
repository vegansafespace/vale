from dependency_injector import containers, providers

from src.components.application import Application
from src.components.voice_category import VoiceCategory
from src.components.voice_hub import VoiceHub
from src.vale import Vale


class Container(containers.DeclarativeContainer):
    # bot
    bot = providers.Singleton(Vale)

    # components
    application = providers.Singleton(Application)
    voice_category = providers.Singleton(VoiceCategory)
    voice_hub = providers.Singleton(VoiceHub)
