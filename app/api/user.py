from fastapi import APIRouter, Depends
from asyncpg import Connection
from app.schemas.user import UserLogin, UserId, UserInfo, CommonResponse
from app.services.user import user_pw_services, user_name_services, user_info_services
from app.db.database import get_db

router = APIRouter()

# 신규 회원가입 비밀번호를 입력했을 때, 해싱된 비밀번호 값을 DB에 저장
@router.post("/uregister", response_model = CommonResponse)
async def uregister(data: UserLogin, conn: Connection = Depends(get_db)):

    return await user_pw_services(conn, data)

# 신규 회원 아이디 중복, not null 검사
@router.post("/ucheck", response_model = CommonResponse)
async def ucheck(data: UserId, conn : Connection = Depends(get_db)):

    return await user_name_services(conn, data)

# 사용자 정보 조회
@router.post("/uinfo", response_model = CommonResponse)
async def uinfo(data: UserLogin, conn: Connection = Depends(get_db)):

    return await user_info_services(conn, data)
