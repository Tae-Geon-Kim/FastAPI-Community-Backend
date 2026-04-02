import os
import uuid
import aiofiles
from asyncpg import Connection
from fastapi import HTTPException, status, UploadFile
from app.schemas.files import *
from app.models.files import *
from app.schemas.user import UserLogin
from app.models.boards import check_boards_owner
from app.core.config import settings

upload_dir = settings.UPLOAD_DIR
# 허용되는 파일 확장자: jpg, jpeg, png, gif, webp, pdf, docx, xlsx, pptx, txt, hwp, zip, 7z
ALLOWED_EXTENSIONS = {'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'application/pdf', 'text/plain',
                        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                        'application/x-hwp', 'application/zip', 'application/x-7z-compressed'}
allow_max_fsize = settings.FILE_MAX_SIZE
allow_max_total_fsize = settings.FILE_TOTAL_MAX_SIZE

# upload_dir 파일 이름이 존재하지 않으면 파일 생성 (있으면 그냥 넘어감)
os.makedirs(upload_dir, exist_ok = True)

# 파일 업로드
async def upload_files_service(conn: Connection, file: UploadFile , data: UserLogin, board_index: int):

    # 로그인 정보 확인
    user_num  = await login(conn, data)

    if user_num is None:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "로그인 정보를 다시 확인해주세요."
        )

    boards_owner = await check_boards_owner(conn, board_index)
    
    # 해당 유저의 게시판이 존재하는지
    if boards_owner is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = f"{data.id}님의 등록된 게사글이 존재하지않습니다."
        )
    
    # 업로드하려고 하는 게시판의 작성자와 로그인한 작성자가 동일한 인물인지
    if boards_owner['user_index'] != user_num:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "본인의 게시글에만 파일을 업로드 할 수 있습니다."
        )

    # 파일명 전체 소문자로 변환
    lower_content_type = file.content_type.lower()

    # 업로드하는 파일이 허용되는 확장자인지 확인
    if lower_content_type not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail = "허용되는 확장자가 아닙니다."
        )
    
    # 개별 파일을 업로드 하기전에 해당 게시판에 파일을 올릴 수 있는지 확인
    # bytes 단위로 먼저 비교하고 출력할 때만 MB로 

    cur_total_fsize = await get_total_fsize(conn, board_index) # 현재 게시판에 올라가 있는 파일 용량의 총합 (bytes)

    # bytes 를 MB 로 바꿀라면 ((1024) * (1024)) 를 나누기

    # file.size : 현재 업로드 하려하는 파일의 용량 (bytes)
    # allow_max_fsize: 업로드 하는 파일 하나의 허용되는 파일 용량 (bytes)
    # allow_max_total_fsize: 하나의 게시판에 업로드 할 수 있는 허용되는 파일 (여러 파일 용량들의 합) 용량 (bytes)

    # 현재 업로드 된 파일의 총 용량 + 업로드 하려는 파일의 용량이 허용되는 크기인지 확인
    if (cur_total_fsize + file.size) > allow_max_totla_fsize:
        raise HTTPException(
            status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
             detail = f"허용하는 파일의 용량을 초과하였습니다. (최대: {(allow_max_total_fsize / (1024 * 1024)):.2f} 현재: {(cur_total_fsize / (1024 * 1024)):.2f} 업로드 파일: {(file.size / (1024 * 1024)):.2f})"
        )

    # 업로드하는 파일의 크기가 허용되는 크기인지 확인
    if file.size > allow_max_fsize:
        raise HTTPException(
            status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail = f"파일 용량이 너무 큽니다. (최대 {(allow_max_fsize / (1024 * 1024)):.2f}MB)"
        )

    # filepath 생성
    _, ext = os.path.splitext(file.filename)
    # os.path.splitext()를 하면 {파일명, 확장자} 형식의 튜플 형태를 반환하지만 현재 파일명 부분은 필요가 없음
    # _를 쓰면 dummy_variable로써 파일명을 무시하게 만들 수 있음. -> ,_: 반대로 확장자를 무시

    filename = f"{uuid.uuid4()}{ext}"
    filepath = os.path.join(upload_dir, filename)

    # 비동기 파일처리
    async with aiofiles.open(filepath, "wb") as out_file:
        content = await file.read()
        await out_file.write(content)
    
    await upload_files_db(conn, file.filename, filename, filepath, file.size, board_index)

    return CommonResponse(message = f"{data.id}님이 요청하신 {file.filename}파일의 업로드 작업이 완료되었습니다.")

# 파일 삭제
async def delete_files_service(conn: Connection, data: UserLogin, board_index: int, files_index: int):

    # 로그인 정보 확인
    user_num = await login(conn, data)

    if user_num is None:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "로그인 정보를 다시 확인해주세요."
        )

    # 해당 User의 게시판이 존재하는지
    boards_owner = await check_boards_owner(conn, board_index)

    if boards_owner is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = f"{data.id}님의 등록된 게시글이 존재하지않습니다."
        )
    
    # 권한 확인
    if boards_owner['user_index'] != user_num:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "권한이 없습니다. 본인 게시글의 파일만 삭제할 수 있습니다."
        )
    
    if await check_files_belong(conn, files_index, board_index) is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "삭제하려는 파일이 이미 삭제되었거나 해당 게시들에 소속되어 있지 않습니다"
            # files_index 와 board_index 매칭 되는 데이터가 존재하지않는다.
        )

    # soft_delete
    await soft_delete_one_file(conn, files_index)

    return CommonResponse(message = f"{data.id}님이 요청하신 삭제 요청이 성공적으로 처리되었습니다.")

# 실제 삭제
async def delete_files_perman(pool):
    async with pool.acquire() as conn:
        await delete_files(conn)

# 한 게시판에 존재하는 모든 파일을 삭제 (게시판은 삭제 x)
async def delete_all_services(conn: Connection, data: UserLogin, board_index: int):

    # 로그인 정보 확인

    user_num = await login(conn, data)

    if user_num is None:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "로그인 정보를 확인해주세요."
        )
    
    # 해당 User의 게시판이 존재하는지

    board_owner = await check_boards_owner(conn, board_index)

    if board_owner is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = f"{data.id}님의 등록된 게시글이 존재하지않습니다."
        )

    # 권한 확인

    if board_owner['user_index'] != user_num:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "권한이 없습니다. 본인 게시글의 파일만 삭제할 수 있습니다."
        )

    # soft delete
    await soft_delete_all_file(conn, board_index)

    return CommonResponse(message = f"{data.id}님이 요청하신 해당 게시물의 모든 파일이 삭제되었습니다.")

# 실제 삭제
async def delete_all_perman(pool):
    async with pool.acquire() as conn:
        await delete_files(conn)