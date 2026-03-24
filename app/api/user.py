from fastapi import APIRouter, Depends
from asyncpg import Connection
from app.schemas import UserCreate
from app.db.database import get_db

router = APIRouter()

# 신규 회원가입 비밀번호를 입력했을 때, 해싱된 비밀번호 값을 DB에 저장
@router.post("/uregister")
async def uregister(data: UserCreate conn: Connection = Depends(get_db)):
    return await user_create_services(conn, data)

# 신규 회원 아이디 중복, not null 검사
@router.post("/ucheck")
async def ucheck(data: UserCreate conn : Connection = Depends(get_db)):

# 사용자 정보 조회
@router.post("/uinfo")
async def uinfo(data: UserCreate conn: Connection = Depends(get_db)):
    return await user_info_services(conn, data)