from motor.motor_asyncio import AsyncIOMotorClient
from src.helpers.env import MONGO_HOST, MONGO_PORT, MONGO_USERNAME, MONGO_PASSWORD


def create_mongodb_client() -> AsyncIOMotorClient:
    if MONGO_USERNAME and MONGO_PASSWORD:
        uri = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/"
    else:
        uri = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/"

    return AsyncIOMotorClient(uri)
