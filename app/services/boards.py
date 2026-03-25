from asyncpg import Connection
from app.schemas.boards import CreateBoard, BoardInfo
from app.schemas.user import UserId
from app.models.boards import insert_boards_db, certain_user_boards_info
from app.models.user import id_duplicate
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

# 특정 사용자의 게시판 목록을 출력 (사용자의 이름 입력 받아서 있음 출력 아님 에러 / 로그인 필요 없음)
async def boards_info_services(conn: Connection, data: UserId):

    user_exist = await id_duplicate(conn, data)

    # 해당 사용자가 존재 x
    if not user_exist:
        return {
            "성공 여부" : "False",
            "메시지" : "해당 사용자가 존재하지않습니다."           
        }

    # 해당 사용자가 존재 / 해당 사용자의 전체 게시글 fetch
    rows = await certain_user_boards_info(conn, data.id)

    # 해당 사용자가 쓴 게시글이 없는 경우
    if not rows:
        return {
            "성공 여부" : "False",
            "메시지" : f"{data.id}의 등록된 게시글이 없습니다."
        }
    
    board_list = [BoardInfo.model_validate(dict(row)) for row in rows]
    
    return {
        "성공 여부" : "True",
        "메시지" : "게시글 조회에 성공하였습니다. 게시판 정보를 출력합니다.",
        "data" : board_list
    }
