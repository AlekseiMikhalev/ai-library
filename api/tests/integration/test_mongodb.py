import pytest

from src.database.mongodb import get_mongodb


@pytest.fixture
async def test_collection():
    mongodb = await get_mongodb()
    db = mongodb["test"]
    collection = db["test_collection"]
    yield collection
    await collection.drop()


@pytest.mark.asyncio
async def test_mongodb_connection(test_collection):
    try:
        result = await test_collection.insert_one({"test": "data"})
        assert result.inserted_id is not None
    except Exception as e:
        pytest.fail(f"MongoDB connection failed: {str(e)}")
