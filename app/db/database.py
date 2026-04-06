import asyncpg
from asyncpg import Connection, Pool
from fastapi import FastAPI, Depends, Request
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.core.config import settings

# DB 점속 정보를 .env 환경 변수로 분리
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db_pool = await asyncpg.create_pool(
        user = settings.DB_USER,
        password = settings.DB_PASSWORD,
        database = settings.DB_NAME,
        host = settings.DB_HOST,
        port = settings.DB_PORT,
        max_size = settings.DB_MAX_SIZE,
        min_size = settings.DB_MIN_SIZE
    )
    print("DB 커넥션 풀이 준비되었습니다!")

    from app.services.user import withdraw_user_perman
    from app.services.boards import delete_boards_perman
    from app.services.files import delete_files_perman

    scheduler = AsyncIOScheduler()
    scheduler.add_job(withdraw_user_perman, 'interval', hours = 3, args = [app.state.db_pool])
    scheduler.add_job(delete_boards_perman, 'interval', hours = 3, args = [app.state.db_pool])
    scheduler.add_job(delete_files_perman, 'interval', hours = 3, args = [app.state.db_pool])
    scheduler.start()

    yield

    if app.state.db_pool:
        scheduler.shutdown()
        await app.state.db_pool.close()
        print("DB 연결이 안전하게 종료되었습니다.")

async def get_db(request : Request):
    # 파일 분리 시 (MVC), app 객체가 정의되지 않은 다른 파일에섣 FastAPI 인스턴스에 접근하기 위해 request 사용
    if request.app.state.db_pool is None:
        raise Exception("DB pool is not initialized")
    
    async with request.app.state.db_pool.acquire() as connection:
        yield connection
