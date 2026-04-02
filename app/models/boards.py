# app/schemas/boards.py 에서 스키마 가져와야함
# depends(get_db)가 빠진 이유: 모델이 FastAPI에 의존하지 않게 해야 코드의 독립성과 재사용성을 유지 가능
from asyncpg import Connection

async def insert_boards_db(conn: Connection, title: str, content: str, user_index: int):

	sql = 'INSERT INTO boards (title, content, user_index) VALUES ($1, $2, $3)'

	return await conn.execute(sql, title, content, user_index)

# 특정 유저의 게시판 정보 조회 (INNER JOIN)
async def certain_user_boards_info(conn: Connection, user_id: str):

	sql = """
		SELECT
			b.index,
			b.title,
			b.content,
			b.reg_date,
			b.update_date,
			u.id,
			COALESCE(
			(SELECT json_agg(json_build_object (
				'index', f.index,
				'original_name', f.original_name,
				'file_size', f.file_size,
				'reg_date', f.reg_date
				))
				FROM files as f
				WHERE f.board_index = b.index
				AND f.deleted_at IS NULL),
				'[]'::json
				) AS files
			FROM boards AS b
			INNER JOIN "user" AS u ON b.user_index = u.index
			WHERE u.id = $1
				AND b.deleted_at IS NULL
				AND u.deleted_at IS NULL
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
			WHERE b.deleted_at IS NULL
			AND u.deleted_at IS NULL
		ORDER BY u.id ASC, b.index DESC
	""" 
	# ORDER BY u.id ASC : 사용자 아이디를 가나나 / ABC 순으로
	# ORDER BY b.index DESC : 게시글 중 가장 번호가 큰 글 (최신) 위로 정렬
	# ASC: 오름차순
	# DESC: 내림차순

	return await conn.fetch(sql)

# 해당 User가 쓴 글인지 확인 (글 번호를 <-> 작성자 번호)
async def check_boards_owner(conn: Connection, boards_index: int):

	sql = 'SELECT user_index FROM boards WHERE index = $1 AND deleted_at IS NULL'

	return await conn.fetchrow(sql, int(boards_index))

# 게시판 제목 변경
async def title_modify(conn: Connection, new_title: str, board_index: int):

	sql = 'UPDATE boards SET title = $1, update_date = NOW() WHERE index = $2'

	return await conn.execute(sql, new_title, board_index)

# 게시판 내용 변경
async def content_modify(conn: Connection, new_content: str, board_index: int):

	sql = 'UPDATE boards SET content = $1, update_date = NOW() WHERE index = $2'

	return await conn.execute(sql, new_content, board_index)

# 게시판 삭제 (실제 삭제 x, deleted_at 상태값만 변경)
async def soft_delete_boards(conn: Connection, boards_index: str):

	sql = 'UPDATE boards SET deleted_at = NOW() WHERE index = $1'

	return await conn.execute(sql, boards_index)

# 게시판 삭제 (실제 삭제)
async def delete_boards(conn: Connection):

	sql = """
		DELETE FROM boards WHERE deleted_at IS NOT NULL
		AND deleted_at <= NOW() - INTERVAL '3 days'
	"""

	return await conn.execute(sql)