from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from api.src.config.settings import app_settings


def get_mongodb() -> AsyncIOMotorDatabase:
    """Get MongoDB client instance."""
    client = AsyncIOMotorClient(app_settings.MONGO_DB_URL)
    return client.get_database(app_settings.MONGO_DB_NAME)
