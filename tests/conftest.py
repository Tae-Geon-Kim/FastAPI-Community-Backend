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

TEST_DB_NAME = "Test_CommunityBackendDB"

os.environ["REDIS_HOST"] = "127.0.0.1"
os.environ["DB_HOST"] = "127.0.0.1"
os.environ["DB_NAME"] = TEST_DB_NAME

# GITHUB_ACTIONS는 깃허브 액션(CI/CD) 서버가 켜지고 코드가 실행되는 순간 깃허브 서버가 컴퓨터에 자동으로 생성하는 기본 환경 변수
# 코드의 정상작동 유무와 상관없이 일단 돌고 있으면 그 값은 항상 "true" (CI/CD 환경이 아니라면 그 값 자체가 존재하지 않으니 "None")
# 즉, GITHUB_ACTIONS 가 "true"이면 github actions에서 돌고 있는것이기 때문에 port = 5432
# true 가 아니라면 (None 이라면) 현재 로컬에서 코드가 돌고 있는것이기 때문에 port = 15432
if os.environ.get("GITHUB_ACTIONS") != "true":
    os.environ["DB_PORT"] = "15432"

from app.main import app
from app.db.database import get_db
from app.db.redis_config import redis_db
from app.core.config import settings
from app.services import files as file_services

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

    async with AsyncClient(
        transport = ASGITransport(
            app = app,
            raise_app_exceptions = True
        ),
        base_url = "http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()

@pytest.fixture(scope="session", autouse=True)
def setup_test_upload_dir():
    TEST_UPLOAD_DIR = "./test_uploads_temp"
    
    if os.path.exists(TEST_UPLOAD_DIR):
        shutil.rmtree(TEST_UPLOAD_DIR)
    os.makedirs(TEST_UPLOAD_DIR, exist_ok=True)
    
    original_upload_dir = file_services.upload_dir
    file_services.upload_dir = TEST_UPLOAD_DIR
    
    yield
    
    if os.path.exists(TEST_UPLOAD_DIR):
        shutil.rmtree(TEST_UPLOAD_DIR)
        
    file_services.upload_dir = original_upload_dir

@pytest_asyncio.fixture(autouse = True)
async def flush_redis():
    await redis_db.flushdb()
    yield
    await redis_db.flushdb()
    await redis_db.connection_pool.disconnect()