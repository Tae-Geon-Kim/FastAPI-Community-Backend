import asyncpg
from asyncpg import Connection, Pool
from fastapi import FastAPI, Depends, Request
from pydantic import BaseModel
from contextlib import asynccontextmanager

class Data(BaseModel):
    name: str
    pw: str 
    title: str
    content: str

# app.on_event() 로 구현한걸 lifespan으로 구현
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db_pool = await asyncpg.create_pool(
        user="cutshion",
        password="cutshion%40",
        database="CommunityBackendDB",
        host="127.0.0.1",
        port=5432,
        min_size=5,
        max_size=10
    )
    print("DB 커넥션 풀이 준비되었습니다!")

    yield

    if app.state.db_pool: 
        await app.state.db_pool.close()
        print("DB 연결이 안전하게 종료되었습니다.")

app = FastAPI(lifespan = lifespan)

async def get_db(request : Request):
    # 파일 분리 시 (MVC), app 객체가 정의되지 않은 다른 파일에섣 FastAPI 인스턴스에 접근하기 위해 request 사용
    if request.app.state.db_pool is None:
        raise Exception("DB pool is not initialized")
    
    async with request.app.state.db_pool.acquire() as connection:
        yield connection


# boards.py
@app.post("/bregister")
async def bregister(data: Data, conn: Connection = Depends(get_db)):
    sql = 'INSERT INTO "boards" (title, content, name) VALUES ($1, $2, $3)'

    try:
        # SQL 실행
        await conn.execute(sql, data.title, data.content, data.name)
        return {"success": True, "message": "게시글 등록 성공!"}
    
    except Exception as e:
        print(f"에러 발생: {str(e)}")
        return {
            "success": False, 
            "message": "게시글 등록 중 오류가 발생했습니다.",
            "detail": str(e) # 실제 에러 내용이 궁금할 때를 위해 추가
        }

# main 함수가 실제로 실행될 때만 실행이 되도록
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


# on_event("startup") / on_event(shutdown) lifespan 으로 바꾸기 (완료)
# db_pool 전역 x -> app.state