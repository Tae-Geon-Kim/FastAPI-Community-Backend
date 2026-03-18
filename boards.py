#boards API
import asyncpg
import asyncio

from database import connect_db
from fastapi import APIRouter
from pydantic import BaseModel
from util import login

router = APIRouter()

class Data(BaseModel):
    name: str
    pw: str
    title: str
    content: str
    
# 게시판 생성 -> reg_date
# 로그인 로직이 완료되어 로그인이 됐을 경우에만 가능
# 제목 지정 (null이면 안되니까 검증) -> 내용 입력 
@router.post("/bregister")
async def bregister(user : Data):
    sql = 'INSERT INTO "boards" (title, content, author) VALUES ($1, $2, $3)'

    if not user.title.strip(): # 제목이 공백이라면
        return {"Message" : "제목에 공백을 사용할 수 없습니다."}

    if await login(user.name, user.pw) == 1: # 로그인에 성공한 경우
        conn = await connect_db()
        try:
            await conn.execute(sql, user.title, user.content, user.name)
            return {"Message" : "게시글 등록에 성공하였습니다."}
        finally:
            await conn.close()
    else: # 로그인에 실패했을 때
        return {"Message" : "로그인에 실패했습니다."}