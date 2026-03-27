# app/schemas/boards.py 에서 스키마 가져와야함
# depends(get_db)가 빠진 이유: 모델이 FastAPI에 의존하지 않게 해야 코드의 독립성과 재사용성을 유지 가능
from asyncpg import Connection
from app.schemas.boards import CreateBoard

async def insert_boards_db(conn: Connection, data: CreateBoard, user_num: int):

	sql = 'INSERT INTO "boards" (title, content, user_index) VALUES ($1, $2, $3)'

	return await conn.execute(sql, data.title, data.content, user_num)

# 특정 유저의 게시판 정보 조회 (INNER JOIN)
async def certain_user_boards_info(conn: Connection, user_id: str):

	sql = """
		SELECT
			b.index,
			b.title,
			b.content,
			b.reg_date,
			b.update_date,
			u.id
			FROM boards AS b
			INNER JOIN "user" AS u 
			ON b.user_index = u.index
			WHERE u.id = $1
			ORDER BY b.index DESC
	"""
	# ORDER BY b.index DESC : 가장 최근에 쓴 글 (가장 큰 번호)이 가장 위로 

	return await conn.fetch(sql, user_id)

# 모든 유저의 게시판 정보 조회 (INNER JOIN)
async def all_user_boards_info(conn: Connection):

	sql = """
		SELECT
		b.index,
		b.title,
		b.content,
		b.reg_date,
		b.update_date,
		u.id AS author
		FROM boards AS b
		INNER JOIN "user" AS u
		ON b.user_index = u.index
		ORDER BY u.id ASC, b.index DESC
	""" 
	# ORDER BY u.id ASC : 사용자 아이디를 가나나 / ABC 순으로
	# ORDER BY b.index DESC : 게시글 중 가장 번호가 큰 글 (최신) 위로 정렬
	# ASC: 오름차순
	# DESC: 내림차순

	return await conn.fetch(sql)

# 게시판 soft 삭제
async def soft_withdraw_boards(conn: Connection, user_index: int):

	sql = 'UPDATE boards SET deleted_at = NOW() WHERE user_index = $1'

	return await conn.execute(sql, user_index)