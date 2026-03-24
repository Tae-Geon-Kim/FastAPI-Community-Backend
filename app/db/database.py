import asyncpg
from asyncpg import Connection, Pool
from fastapi import FastAPI, Depends, Request
from contextlib import asynccontextmanager

# TODO: 보안을 위해 하드코딩된 DB 접속 정보를 .env 환경 변수로 분리할 것
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db_pool = await asyncpg.create_pool(
        user="cutshion",
        password="cutshion@",
        database="CommunityBackendDB",
        host="127.0.0.1",
        port=5432,
        min_size=5,
        max_size=10
    )
    print("DB 커넥션 풀이 준비되었습니다!")

    yield

    if app.state.db_pool: 
        await app.state.db_pool.close()
        print("DB 연결이 안전하게 종료되었습니다.")

async def get_db(request : Request):
    # 파일 분리 시 (MVC), app 객체가 정의되지 않은 다른 파일에섣 FastAPI 인스턴스에 접근하기 위해 request 사용
    if request.app.state.db_pool is None:
        raise Exception("DB pool is not initialized")
    
    async with request.app.state.db_pool.acquire() as connection:
        yield connection
