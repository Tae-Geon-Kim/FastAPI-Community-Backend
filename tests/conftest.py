import os
import shutil
import pytest
import pytest_asyncio
import asyncpg
from httpx import AsyncClient, ASGITransport
from fastapi import Request

# 프로젝트 파일 임포트
from app.main import app 
from app.db.database import get_db
from app.core.config import settings

# 파일 서비스 모듈 임포트 (업로드 경로를 가로채기 위함)
from app.services import files as files_service 

# 테스트용 데이터베이스 이름
TEST_DB_NAME = "Test_CommunityBackendDB" 

@pytest_asyncio.fixture(scope="session")
async def db_pool():
# 테스트용 DB 커넥션 풀 생성

    pool = await asyncpg.create_pool(
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=TEST_DB_NAME,
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        max_size=5,
        min_size=1
    )
    yield pool
    await pool.close()

@pytest_asyncio.fixture()
async def db_connection(db_pool):
# 테스트가 끝날때마다 DB 초기화

    async with db_pool.acquire() as connection:
        transaction = connection.transaction()
        await transaction.start() # 트랜잭션 시작 (데이터 저장 보류)
        
        yield connection # 테스트 코드에 커넥션 전달
        
        await transaction.rollback() # 테스트 종료 후 무조건 롤백! (초기화)

@pytest_asyncio.fixture()
async def client(db_connection):

    # 기존 get_db 대신 실행될 가짜(Override) 함수
    async def override_get_db():
        yield db_connection

    # app의 의존성 가로채기
    app.dependency_overrides[get_db] = override_get_db

    # 비동기 테스트 클라이언트 생성 (httpx)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    # 테스트가 끝나면 가로챘던 의존성 복구
    app.dependency_overrides.clear()

@pytest.fixture(scope="session", autouse=True)
def setup_test_upload_dir():
# 파일 업로드 테스트시 쌓이는 테스트 파일들을 임시 파일에 저장 후 테스트가 끝나면 삭제

    # 실제 운영 파일과 섞이지 않도록 '테스트 전용' 폴더 이름 지정
    TEST_UPLOAD_DIR = "./test_uploads_temp"
    
    # 만약 이전 테스트에서 찌꺼기가 남았다면 지우고, 폴더를 새로 만듦
    if os.path.exists(TEST_UPLOAD_DIR):
        shutil.rmtree(TEST_UPLOAD_DIR)
    os.makedirs(TEST_UPLOAD_DIR, exist_ok=True)
    
    # services/files.py 의 upload_dir 변수를 강제로 테스트 폴더로 바꿔치기 (Monkeypatch)
    original_upload_dir = files_service.upload_dir
    files_service.upload_dir = TEST_UPLOAD_DIR
    
    # 이 시점에서 테스트 실행
    yield 
    # 테스트 종료 (디스크에 테스트 파일들 있음)
    
    # 테스트 끝나면 테스트 파일이 담긴 테스트 폴더 전체 삭제
    if os.path.exists(TEST_UPLOAD_DIR):
        shutil.rmtree(TEST_UPLOAD_DIR)
        
    # 다음 실행을 위해 원래 경로로 얌전히 되돌려 놓음
    files_service.upload_dir = original_upload_dir