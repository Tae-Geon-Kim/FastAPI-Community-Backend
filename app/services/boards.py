from asyncpg import Connection
from app.schemas.boards import CreateBoard
from app.models.boards import insert_boards_db
from app.services.util import login

async def create_boards_services(conn: Connection, data: CreateBoard):

    # 게시판 제목이 빈 문자열인 경우
    if not data.title.strip():
        return {
            "성공 여부" : "False",
            "메시지" : "게시판 제목에는 빈 문자열을 사용할 수 없습니다."
        }

    # 게시판 내용이 빈 문자열인 경우
    if not data.content.strip():
        return {
            "성공 여부" : "False",
            "메시지" : "게시판 내용에는 빈 문자열을 사용할 수 없습니다."
        }
    
    user_num = await login(conn, data)
    # 로그인 성공 시 user_num 에는 사용자의 index 가
    # 로그인 실패 시 None

    # 로그인에 실패한 경우
    if user_num is None:
        return {
            "성공 여부" : "False",
            "메시지" : "로그인 정보를 다시 확인해주세요."
        }

    # 게시판을 저장할 때 user_num도 같이 저장
    await insert_boards_db(conn, data, user_num)

    return {
        "성공 여부" : "True",
         "메시지" : "게시판을 생성을 성공적으로 완료했습니다."       
    }




