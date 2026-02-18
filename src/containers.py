from logging import Logger

from dependency_injector import containers, providers
from dependency_injector.providers import Singleton

from src.logger import logger as log
from src.components.application import Application
from src.components.application_service import ApplicationService
from src.components.voice_category import VoiceCategory
from src.components.voice_hub import VoiceHub
from src.helpers.mongodb import create_mongodb_client
from src.vale import Vale


class Container(containers.DeclarativeContainer):
    # logger
    logger: providers.Object[Logger] = providers.Object(log)

    # db
    db_client = providers.Singleton(create_mongodb_client)

    # bot
    bot = providers.Singleton(Vale, logger=logger)

    # components
    application_service = providers.Singleton(ApplicationService, db_client=db_client)
    application = providers.Singleton(Application)
    voice_category = providers.Singleton(VoiceCategory)
    voice_hub = providers.Singleton(VoiceHub)
