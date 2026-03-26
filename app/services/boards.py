from asyncpg import Connection
from fastapi import HTTPException
from collections import defaultdict
from app.schemas.boards import *
from app.models.boards import *
from app.schemas.user import UserId
from app.models.user import id_duplicate
from app.services.auth import login

async def create_boards_services(conn: Connection, data: CreateBoard):

    # 게시판 제목이 빈 문자열인 경우
    if not data.title.strip():
        raise HTTPException(status_code = 400, detail = "게시판 제목에는 빈 문자열을 사용할 수 없습니다.")

    # 게시판 내용이 빈 문자열인 경우
    if not data.content.strip():
        raise HTTPException(status_code = 400, detail = "게시판 내용에는 빈 문자열을 사용할 수 없습니다.")
    
    user_num = await login(conn, data)
    # 로그인 성공 시 user_num 에는 사용자의 index 가
    # 로그인 실패 시 None

    # 로그인에 실패한 경우
    if user_num is None:
        raise HTTPException(status_code = 401, detail = "로그인 정보를 다시 확인해주세요.")

    # 게시판을 저장할 때 user_num도 같이 저장
    await insert_boards_db(conn, data, user_num)

    return CommonResponse(message = "게시판이 생성되었습니다.")

# 특정 사용자의 게시판 목록을 출력 (사용자의 이름 입력 받아서 있음 출력 아님 에러 / 로그인 필요 없음)
async def certain_boards_info_services(conn: Connection, data: UserId):

    user_exist = await id_duplicate(conn, data)

    # 해당 사용자가 존재 x
    if not user_exist:
        raise HTTPException(status_code = 404, detail = "해당 사용자가 존재하지않습니다.")

    # 해당 사용자가 존재 / 해당 사용자의 전체 게시글 fetch
    # DB에서 데이터를 가져오면 asyncpg는 Record형태로 데이터를 받아옴.
    rows = await certain_user_boards_info(conn, data.id)

    # 해당 사용자가 쓴 게시글이 없는 경우
    if not rows:
        raise HTTPException(status_code = 404, detail = f"{data.id}님의 등록된 게시글이 존재하지않습니다.")
    
    board_list = [BoardInfo.model_validate(dict(row)) for row in rows]
    # Pydantic이 Record 객체의 속성을 인식하지 못하므로 dict로 변환 후 검증
    # DB에서 가져온 모든 Record 객체를 각각 dict로 변환하여 리스트 형태로 반환

    return CommonResponse(message = f"{data.id}님의 게시판을 출력합니다.", data = board_list)


# 전체 게시판을 출력 (사용자 별로 / 로그인 필요 없음)
async def all_boards_info_services(conn: Connection):

    rows = await all_user_boards_info(conn)
    # DB에서 데이터를 가져오면 asyncpg는 Record형태로 데이터를 받아옴.

    # boards 테이블에 게시판이 아예 하나도 존재하지 않을 때
    if not rows:
        raise HTTPException(status_code = 404, detail = "등록된 게시글이 존재하지않습니다.")
    
    grouped_dict =defaultdict(list)
    # 빈 딕셔너리 생성

    for row in rows:
        row_dict = dict(row)
        author_id = row_dict['author']
        grouped_dict[author_id].append(row_dict)

    final_data = []

    for author_name, post_list in grouped_dict.items():
        user_group = AllBoardInfoResponse(author = author_name, posts = post_list)

        final_data.append(user_group)
    
    return CommonResponse(
        message = "전체 게시글을 사용자별로 분류하여 출력합니다.",
        data = final_data
    )