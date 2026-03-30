from fastapi import APIRouter, Depends, status
from asyncpg import Connection
from app.schemas.user import *
from app.services.user import *
from app.db.database import get_db

router = APIRouter()

# 신규 회원가입 비밀번호를 입력했을 때, 해싱된 비밀번호 값을 DB에 저장
@router.post("/uRegister", response_model = CommonResponse, status_code = status.HTTP_200_OK)
async def uregister(data: UserLogin, conn: Connection = Depends(get_db)):

    return await user_pw_services(conn, data)

# 신규 회원 아이디 중복, not null 검사
@router.post("/uCheck", response_model = CommonResponse, status_code = status.HTTP_200_OK)
async def ucheck(data: UserId, conn : Connection = Depends(get_db)):

    return await user_name_services(conn, data)

# 사용자 정보 조회
@router.post("/uInfo", response_model = CommonResponse, status_code = status.HTTP_200_OK)
async def uinfo(data: UserLogin, conn: Connection = Depends(get_db)):

    return await user_info_services(conn, data)

# 사용자 회원탈퇴 
@router.post("/withdraw", response_model = CommonResponse, status_code = status.HTTP_200_OK)
async def withdraw(data: UserLogin, conn: Connection = Depends(get_db)):

    return await user_withdraw_services(conn, data)

# 사용자 아이디 변경
@router.post("/idModify", response_model = CommonResponse, status_code = status.HTTP_200_OK)
async def modify(data: ModiId, conn: Connection = Depends(get_db)):

    return await userId_modify_services(conn, dataa)