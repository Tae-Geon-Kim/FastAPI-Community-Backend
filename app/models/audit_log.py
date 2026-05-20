import json
from asyncpg import Connection

# audit_log 테이블에 정보 삽입
async def insert_audit_log(conn: Connection, action: str, target_type: str, target_index: int, actor_user_index: int, actor_user_id: str, detail: dict = None):

    sql = """
        INSERT INTO audit_logs
        (action, target_type, target_index, actor_user_index, actor_user_id, detail)
        VALUES($1, $2, $3, $4, $5, $6::jsonb)
    """

    detail_json = json.dumps(detail) if detail else None

    return await conn.execute(sql, action, target_type, target_index, actor_user_index, actor_user_id, detail)