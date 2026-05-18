import os
import shutil
import pytest
import pytest_asyncio
import asyncpg
import redis.asyncio as redis
from httpx import AsyncClient, ASGITransport

from fastapi import Request, Response
from fastapi_limiter.depends import RateLimiter

async def mock_rate_limit(self, request: Request, response: Response):
    pass
RateLimiter.__call__ = mock_rate_limit

os.environ["REDIS_HOST"] = "127.0.0.1"

if os.environ.get("GITHUB_ACTIONS") != "true":
    os.environ["DB_PORT"] = "15432"

from app.main import app
from app.db.database import get_db
from app.db.redis_config import redis_db
from app.core.config import settings
from app.services import files as files_service 

TEST_DB_NAME = "Test_CommunityBackendDB"

@pytest_asyncio.fixture()
async def db_pool():
    pool = await asyncpg.create_pool(
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=TEST_DB_NAME,
        host="127.0.0.1",
        port=settings.DB_PORT,
        max_size=5,
        min_size=1
    )
    yield pool
    await pool.close()

@pytest_asyncio.fixture()
async def db_connection(db_pool):
    async with db_pool.acquire() as connection:
        transaction = connection.transaction()
        await transaction.start() 
        yield connection 
        await transaction.rollback() 

@pytest_asyncio.fixture()
async def client(db_connection):

    async def override_get_db():
        yield db_connection

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()

@pytest.fixture(scope="session", autouse=True)
def setup_test_upload_dir():
    TEST_UPLOAD_DIR = "./test_uploads_temp"
    
    if os.path.exists(TEST_UPLOAD_DIR):
        shutil.rmtree(TEST_UPLOAD_DIR)
    os.makedirs(TEST_UPLOAD_DIR, exist_ok=True)
    
    original_upload_dir = files_service.upload_dir
    files_service.upload_dir = TEST_UPLOAD_DIR
    
    yield 
    
    if os.path.exists(TEST_UPLOAD_DIR):
        shutil.rmtree(TEST_UPLOAD_DIR)
        
    files_service.upload_dir = original_upload_dir

@pytest_asyncio.fixture(autouse = True)
async def flush_redis():
    await redis_db.flushdb()
    yield
    await redis_db.flushdb()
    await redis_db.connection_pool.disconnect()