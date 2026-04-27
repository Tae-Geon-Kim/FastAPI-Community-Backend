import uvicorn
import traceback
import time
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import lifespan
from app.api.boards import router as boards_router
from app.api.user import router as user_router
from app.api.files import router as files_router
from app.core.logger import logger

app = FastAPI(lifespan = lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React 기본 포트
        "http://localhost:5173",  # Vite 기본 포트
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_request(request: Request, call_next):
    try:
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(f"Request URL: {request.url.path}")
        logger.info(f"Response status code: {response.status_code}")
        response.headers["X-Process-Time"] = str(process_time)

        return response
    except Exception as e:
        logger.error(f"error on {request.url.path}: {e}\n {traceback.format_exc()}")

        return Response(content = "Internal Server Error", status_code = 500)

# user 테이블에 관련된 라우터 합치기
app.include_router(user_router, prefix = "/users", tags = ["Users"])

# boards 테이블에 관련된 라우터 합치기
app.include_router(boards_router, prefix = "/boards", tags = ["Boards"])

# file 업로드 관련돤 라우터 합치기
app.include_router(files_router, prefix = "/files", tags = ["Files"])

if __name__ == "__main__":
        uvicorn.run(app, host="0.0.0.0", port=8000) 