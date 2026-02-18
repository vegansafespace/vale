import logging
import sys
from src.helpers.env import DEBUG

# Use a custom logger name to distinguish bot logs from library logs
logger = logging.getLogger('vale')
logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)

# Create a handler to print to stdout
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Also configure the discord library logger if needed
discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.INFO)
discord_logger.addHandler(handler)
