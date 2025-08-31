import certifi
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

client = None

async def get_db():
    db = client[settings.DATABASE_NAME]
    try:
        yield db
    finally:
        pass

async def init_db():
    global client
    client = AsyncIOMotorClient(settings.MONGO_URI, tls=True, tlsCAFile=certifi.where())

async def close_db():
    global client
    if client:
        client.close()