import uvicorn
import traceback
import time
import logging
import redis.asyncio as redis
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter
from app.db.database import create_db_pool
from app.api.boards import router as boards_router
from app.api.user import router as user_router
from app.api.files import router as files_router
from app.api.auth import router as auth_router
from app.api.admin import router as admin_router
from app.core.logger import logger
from app.core.config import redis_settings
from app.core.scheduler import start_scheduler, stop_scheduler
responses
@asynccontextmanager
async def lifespan(app: FastAPI):

    app.state.db_pool = await create_db_pool()
    logger.info("DB 커넥션 풀 준비 끝")

    redis_pw = redis_settings.REDIS_PASSWORD
    redis_url = f"redis://:{redis_pw}@redis-cache-container:6379/1" if redis_pw else "redis://redis-cache-container:6379/1"
        
    redis_connection = redis.from_url(
        redis_url,
        encoding = "utf-8",
        decode_respomese = True
    )   

    await FastAPILimiter.init(redis_connection)
    await start_scheduler(app.state.db_pool)
    logger.info("Redis 및 FastAPI Rate Limiter 세팅 완료")

    yield

    await stop_scheduler()
    await redis_connection.close()

    if app.state.db_pool:
        await app.state.db_pool.close()
        logger.info("DB 연결 종료")

app = FastAPI(lifespan = lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React 기본 포트
        "http://localhost:5173",  # Vite 기본 포트
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_request(request: Request, call_next):
    
    try:
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(f"Request URL: {request.url.path}")
        logger.info(f"Response status code: {response.status_code}")
        response.headers["X-Process-Time"] = str(process_time)

        return response
    except Exception as e:
        logger.error(f"error on {request.url.path}: {e}\n {traceback.format_exc()}")

        return Response(content = "서버 에러가 발생했습니다.", status_code = 500)

@app.middleware("http")
async def add_cache_control_header(request: Request, call_next):

    response = await call_next(request)

    # 모든 Method 무조건 캐시 금지
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        
    return response

app.include_router(admin_router, prefix = "/admin", tags = ["Admin"])
app.include_router(auth_router, prefix = "/auth", tags = ["Auth"])
app.include_router(user_router, prefix = "/users", tags = ["Users"])
app.include_router(boards_router, prefix = "/boards", tags = ["Boards"])
app.include_router(files_router, prefix = "/files", tags = ["Files"])

if __name__ == "__main__":
        uvicorn.run(app, host="0.0.0.0", port=8000) 