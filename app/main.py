from fastapi import FastAPI
from app.db.database import lifespan
from app.api.boards import router as boards_router
from app.api.user import router as user_router
from app.api.files import router as files_router

app = FastAPI(lifespan = lifespan)

# user 테이블에 관련된 라우터 합치기
app.include_router(user_router, prefix = "/user", tags = ["User"])

# boards 테이블에 관련된 라우터 합치기
app.include_router(boards_router, prefix = "/boards", tags = ["Boards"])

# file 업로드 관련돤 라우터 합치기
app.include_router(files_router, prefix = "/files", tags = ["Files"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
