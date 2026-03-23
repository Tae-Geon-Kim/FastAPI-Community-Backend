# app/schemas/boards.py 에서 스키마 가져와야함
# depends(get_db)가 빠진 이유: 모델이 FastAPI에 의존하지 않게 해야 코드의 독립성과 재사용성을 유지 가능
from asyncpg import Connection
from app.schemas.boards import CreateBoard

async def insert_boards_db(conn: Connection, data: CreateBoard):
	sql = 'INSERT INTO "boards" (title, content, name) VALUES ($1, $2, $3)'

	return await conn.execute(sql, data.title, data.content, data.name)