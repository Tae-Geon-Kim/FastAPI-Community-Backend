import os
import uuid
import aiofiles
from asyncpg import Connection
from fastapi import HTTPException, status, UploadFile
from datetime import datetime, timezone, timedelta
from app.schemas.files import DeleteFile, DeleteAllFile, RestoreFile, RestoreAllFile
from app.schemas.user import UserLogin
from app.schemas.common import CommonResponse
from app.models.files import (
    get_total_fsize, upload_files_db,
    check_deleted_file_belong, check_undeleted_file_belong,
    soft_delete_one_file, soft_delete_all_board_files, get_file_belong,
    get_softDelete_fsize, restore_one_file, check_board_deleted_files_exist,
    get_total_softDelete_fsize, restore_all_board_files, get_deleted_file_info,
    get_delete_file_path, delete_files, user_get_restorable_fsize, user_restore_all_restorable_files
)
from app.models.boards import check_boards_owner, update_total_board_fsize
from app.models.user import get_user_id_pw
from app.models.audit_log import insert_audit_log
from app.core.config import settings
from app.core.security import verify

upload_dir = settings.UPLOAD_DIR

# 허용되는 파일 확장자: jpg, jpeg, png, gif, webp, pdf, docx, xlsx, pptx, txt, zip
ALLOWED_EXTENSIONS = {
    'image/jpeg', 'image/png', 'image/gif', 'image/webp',

    'application/pdf', 'text/plain',

    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',

    'application/zip'
}
allow_max_fsize = settings.FILE_MAX_SIZE
allow_max_total_fsize = settings.FILE_TOTAL_MAX_SIZE

# upload_dir 파일 이름이 존재하지 않으면 파일 생성 (있으면 그냥 넘어감)
os.makedirs(upload_dir, exist_ok = True)

# 파일 업로드
async def upload_files_services(file: UploadFile, board_index: int, conn: Connection, current_user: dict):

    user_info = await get_user_id_pw(conn, current_user['index'])

    boards_owner = await check_boards_owner(conn, board_index)
    
    # 해당 유저의 게시판이 존재하는지
    if boards_owner is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = f"{user_info['id']}님의 등록된 게시글이 존재하지않습니다."
        )
    
    # 업로드하려고 하는 게시판의 작성자와 로그인한 작성자가 동일한 인물인지
    if boards_owner != current_user['index']:
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
    cur_total_fsize = cur_total_fsize or 0

    # bytes 를 MB 로 바꿀라면 ((1024) * (1024)) 를 나누기

    # file.size : 현재 업로드 하려하는 파일의 용량 (bytes)
    # allow_max_fsize: 업로드 하는 파일 하나의 허용되는 파일 용량 (bytes)
    # allow_max_total_fsize: 하나의 게시판에 업로드 할 수 있는 허용되는 파일 (여러 파일 용량들의 합) 용량 (bytes)

    # 현재 업로드 된 파일의 총 용량 + 업로드 하려는 파일의 용량이 허용되는 크기인지 확인
    if (cur_total_fsize + file.size) > allow_max_total_fsize:
        raise HTTPException(
            status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
             detail = f"업로드시, 한 게시판에 업로드 할 수 있는 총 파일 용량을 초과합니다. (최대: {(allow_max_total_fsize / (1024 * 1024)):.2f}MB 현재: {(cur_total_fsize / (1024 * 1024)):.2f}MB 업로드 파일: {(file.size / (1024 * 1024)):.2f}MB)"
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
    
    async with conn.transaction():
        new_file_index = await upload_files_db(conn, file.filename, filename, filepath, file.size, board_index)
        new_total_fsize = await get_total_fsize(conn, board_index)
        await update_total_board_fsize(conn, new_total_fsize, board_index)
        await insert_audit_log(
            conn = conn,
            action = "UPLOAD",
            target_type = "FILES",
            target_index = new_file_index,
            actor_user_index = current_user['index'],
            actor_user_id = current_user['id'],
            detail = {
                "original_filename": file.filename,
                "file_size_bytes": file.size
            }
        )

    return CommonResponse(message = f"{user_info['id']}님이 요청하신 {file.filename}파일의 업로드 작업이 완료되었습니다.")

# 단일 파일 삭제
async def delete_files_services(file_index: int, data: DeleteFile, conn: Connection, current_user: dict):

    user_info = await get_user_id_pw(conn, current_user['index'])

    board_index = await get_file_belong(conn, file_index)

    if not verify(data.password, user_info['password']):
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "비밀번호가 일치하지 않습니다."
        )

    # 해당 User의 게시판이 존재하는지
    boards_owner = await check_boards_owner(conn, board_index)

    if boards_owner is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = f"{user_info['id']}님의 등록된 게시글이 존재하지않습니다."
        )
    
    if boards_owner != current_user['index']:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "권한이 없습니다."
        )
    
    if await check_undeleted_file_belong(conn, file_index, board_index) is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "삭제하려는 파일이 이미 삭제되었거나 해당 게시글이 등록되어 있지 않습니다."
            # file_index 와 board_index 가 매칭되는 데이터가 존재하지 않는다.
        )
    
    async with conn.transaction():
        # soft delete
        await soft_delete_one_file(conn, "USER", file_index)
        new_total_fsize = await get_total_fsize(conn, board_index) # 용량 값이 bytes 단위로 저장
        new_total_fsize = new_total_fsize or 0
        await update_total_board_fsize(conn, new_total_fsize, board_index)
        await insert_audit_log(
            conn = conn,
            action = "DELETE",
            target_type = "FILES",
            target_index = file_index,
            actor_user_index = current_user['index'],
            actor_user_id = current_user['id'],
            detail = {

            }
        )

    return CommonResponse(message = f"{user_info['id']}님이 요청하신 삭제 요청이 성공적으로 처리되었습니다. 새로운 전체 용량: {(new_total_fsize / (1024 * 1024)):.2f}MB")

# 한 게시판에 존재하는 모든 파일을 삭제 (게시판은 삭제 x)
async def delete_all_services(board_index: int, data: DeleteAllFile, conn: Connection, current_user: dict):
    
    user_info = await get_user_id_pw(conn, current_user['index'])

    if not verify(data.password, user_info['password']):
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "비밀번호가 일치하지 않습니다."
        )

    board_owner = await check_boards_owner(conn, board_index)

    if board_owner is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = f"{user_info['id']}님의 등록된 게시글이 존재하지않습니다."
        )
    
    if board_owner != current_user['index']:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "권한이 없습니다."
        )

    async with conn.transaction():
        # soft delete
        await soft_delete_all_board_files(conn, "USER", board_index)
        await update_total_board_fsize(conn, 0, board_index)
        await insert_audit_log(
            conn = conn,
            action = "DELETE_ALL",
            target_type = "BOARD_FILES",
            target_index = board_index,
            actor_user_index = current_user['index'],
            actor_user_id = current_user['id'],
            detail = {
                "reason": "사용자 본인 요청에 의한 게시판 파일 전체 삭제 (soft delete)"
            }
        )

    return CommonResponse(message = f"{user_info['id']}님이 요청하신 해당 게시물의 모든 파일이 삭제되었습니다.")

# 삭제된 단일 파일 복구 (용량 재계산) / 게시판은 삭제 상태 x
async def restore_file_services(file_index: int, data: RestoreFile, conn: Connection, current_user: dict):

    # 파일 소속 게시판 확인 (파일 존재 여부 확인)
    board_index = await get_file_belong(conn, file_index)
    if board_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="요청하신 파일이 존재하지 않습니다."
        )

    # 유저 비밀번호 검증
    user_id_pw = await get_user_id_pw(conn, current_user['index'])
    if not verify(data.password, user_id_pw['password']):
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "비밀번호가 일치하지 않습니다."
        )

    # 소유자 권한 검사
    boards_owner = await check_boards_owner(conn, board_index)
    if boards_owner != current_user['index']:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "권한이 없습니다."
        )

    # 특정 파일의 deleted_at, deleted_by 값을 가져온다
    check_file = await get_deleted_file_info(conn, file_index)
    if check_file is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "요청하신 파일이 복구 가능한(삭제된) 상태가 아닙니다."
        )

    cur_total_fsize = await get_total_fsize(conn, board_index)
    cur_total_fsize = cur_total_fsize or 0

    softDelete_fsize = await get_softDelete_fsize(conn, file_index)
    softDelete_fsize = softDelete_fsize or 0

    if softDelete_fsize + cur_total_fsize > allow_max_total_fsize:
        raise HTTPException(
            status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail = f"해당 파일 복구시, 한 게시판에 업로드 할 수 있는 총 파일 용량을 초과합니다. (최대: {(allow_max_total_fsize / (1024 * 1024)):.2f}MB, 현재: {(cur_total_fsize / (1024 * 1024)):.2f}MB 복구: {(softDelete_fsize / (1024 * 1024)):.2f}MB)"
        )
    
    time_diff = datetime.now(timezone.utc) - check_file['deleted_at'].replace(tzinfo = timezone.utc)

    if time_diff > timedelta(days = 7):
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = f"삭제 처리를 한지 7일이 경과하여 {file_index}번 파일을 복구 시킬 수 없습니다."
        )
    
    if check_file['deleted_by'] != "USER":
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "관리자에 의해 삭제 처리된 파일을 일반 유저가 임의로 복구 시킬 수 없습니다."
        )
        
    async with conn.transaction():
        await restore_one_file(conn, file_index)
        new_total_fsize = await get_total_fsize(conn, board_index)
        await update_total_board_fsize(conn, new_total_fsize, board_index)
        await insert_audit_log(
            conn = conn,
            action = "RESTORE",
            target_type = "FILE",
            target_index = file_index,
            actor_user_index = current_user['index'],
            actor_user_id = current_user['id'],
            detail = {
                "reason": "사용자 본인 요청에 의한 단일 파일 복구"
            }
        )
    
    return CommonResponse(message = f"{user_id_pw['id']}님이 요청하신 파일이 복구되었습니다. 새로운 전체 용량: {(new_total_fsize / (1024 * 1024)):.2f}MB")

# 삭제된 파일 일괄 복구 (용량 재계산) / 게시판은 삭제 상태 x)
async def restore_all_file_services(board_index: int, data: RestoreAllFile, conn: Connection, current_user: dict):

    user_info = await get_user_id_pw(conn, current_user['index'])
    # user의 index 값을 통해서 아이디, 비밀번호를 가져온다.

    if not verify(data.password, user_info['password']):
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "비밀번호가 일치하지 않습니다."
        )
    
    boards_owner = await check_boards_owner(conn, board_index)
    # 삭제 처리되지 않은 board_index 번 게시판의 작성자의 index 값 fetchval
    
    if boards_owner != current_user['index']:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "권한이 없습니다."
        )

    restore_files_belong = await check_board_deleted_files_exist(conn, board_index)
    # 특정 게시판에 복구 할 수 있는 파일, 즉 삭제 처리된 (soft deleted) 파일이 하나라도 존재하는지 확인

    if restore_files_belong is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "해당 게시판에는 복구 가능한 파일이 존재하지 않습니다."
        )

    # 현재 특정 게시판에 업로드되어 있는 삭제 처리되지 않은 파일들의 총 합
    cur_total_fsize = await get_total_fsize(conn, board_index)
    cur_total_fsize = cur_total_fsize or 0

    # USER 권한으로 특정 게시판에서 복구 가능한 파일 용량의 총 합 (복구는 삭제처리된지 7일이내만 / 삭제처리 100일 후 스케줄러 hard delete)
    user_restorable_fsize = await user_get_restorable_fsize(conn, board_index)
    user_restorable_fsize = user_restorable_fsize or 0

    if user_restorable_fsize == 0:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "해당 게시판에 복구 가능한 파일이 존재하지 않습니다."
        )

    if cur_total_fsize  + user_restorable_fsize > allow_max_total_fsize:
        raise HTTPException(
            status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail = f"복구를 진행할 시, 한 게시판에 업로드 할 수 있는 총 파일 용량을 초과합니다. (최대: {(allow_max_total_fsize / (1024 * 1024)):.2f}MB , 현재: {(cur_total_fsize / (1024 * 1024)):.2f}MB , 복구: {(user_restorable_fsize / (1024 * 1024)):.2f}MB)"
        )

    async with conn.transaction():
        # 파일 복구 & 용량 계산
        await user_restore_all_restorable_files(conn, board_index)
        new_total_fsize = await get_total_fsize(conn, board_index)
        new_total_fsize = new_total_fsize or 0
        await update_total_board_fsize(conn, new_total_fsize, board_index)
        await insert_audit_log(
            conn = conn,
            action = "RESTORE_ALL",
            target_type = "BOARD_FILES",
            target_index = board_index,
            actor_user_index = current_user['index'],
            actor_user_id = current_user['id'],
            detail = {
                "reason": "사용자 본인 요청으로 게시판 파일 전체 일괄 복구",
                "new_board_size": int(new_total_fsize)
            }

        )

    return CommonResponse(message = f"{user_info['id']}님이 요청하신 해당 게시판의 모든 파일을 복구하였습니다. 새로운 전체 용량: {(new_total_fsize / (1024 * 1024)):.2f}MB")

# DB에서 실제로 삭제된 파일을 컴퓨터 메모리상에서 삭제
async def delete_files_perman(pool):
    async with pool.acquire() as conn:
        await delete_files_perman_services(conn)

async def delete_files_perman_services(conn: Connection):

    file_path_record = await get_delete_file_path(conn)

    for record in file_path_record:
        file_path = record['file_path']
        if not os.path.exists(file_path):
            print("파일이 이미 삭제되었거나 존재하지않습니다.")
            continue
        try:
            os.remove(file_path)
            print("파일 삭제에 성공하였습니다.")
        except Exception as e:
            print("파일 삭제에 실패하였습니다.")

    await delete_files(conn)