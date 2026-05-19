import asyncpg
import logging
from asyncpg import Connection, Pool
from fastapi import FastAPI, Depends, Request, status, HTTPException
from contextlib import asynccontextmanager
from app.core.config import settings

async def create_db_pool():
    return await asyncpg.create_pool(
        user = settings.DB_USER,
        password = settings.DB_PASSWORD,
        database = settings.DB_NAME,
        host = settings.DB_HOST,
        port = settings.DB_PORT,
        max_size = settings.DB_MAX_SIZE,
        min_size = settings.DB_MIN_SIZE
    )

# app 객체가 정의되지 않은 파일에서 FastAPI 인스턴스에 접근하기 위해 request 사용
async def get_db(request : Request):

    if request.app.state.db_pool is None:
        raise HTTPException(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = "db pool이 초기화되지 않았습니다."
        )

    async with request.app.state.db_pool.acquire() as connection:
        yield connection
