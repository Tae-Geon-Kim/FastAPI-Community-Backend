import pytest
from httpx import AsyncClient

# 현재 파일의 모든 테스트 함수를 비동기(async)로 실행하도록 설정
pytestmark = pytest.mark.asyncio

# ==========================================
# 미들웨어 동작 및 X-Process-Time 헤더 검증
# ==========================================
async def test_middleware_process_time(client: AsyncClient):
    """
    main.py에 작성된 커스텀 미들웨어가 정상 작동하여, 
    응답 헤더에 'X-Process-Time' 값을 잘 끼워 넣어주는지 확인합니다.
    """
    # 아무 존재하는 엔드포인트(예: docs)나 찔러봅니다.
    res = await client.get("/docs")
    
    assert res.status_code == 200
    # 응답 헤더에 미들웨어가 넣어준 값이 존재하는지 확인
    assert "x-process-time" in res.headers
    # 그 값이 0초 이상인지 확인 (정상적으로 시간이 계산되었는지)
    assert float(res.headers["x-process-time"]) > 0.0
    
    print(f"\n[성공] 미들웨어 동작 확인 (소요 시간: {res.headers['x-process-time']}초)")


# ==========================================
# Swagger API 문서(/docs) 렌더링 테스트
# ==========================================
async def test_api_docs_accessible(client: AsyncClient):
    """
    FastAPI의 기본 API 문서 페이지가 정상적으로 열리는지 확인합니다.
    (모든 라우터(User, Boards, Files)가 충돌 없이 app에 잘 붙었다는 증거입니다.)
    """
    res = await client.get("/docs")
    
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    print("[성공] API 문서 페이지 정상 렌더링 확인")


# ==========================================
# 글로벌 404 에러 핸들링 & 미들웨어 로그 검증
# ==========================================
async def test_404_not_found(client: AsyncClient):
    """
    서버에 존재하지 않는 이상한 URL로 요청을 보냈을 때,
    404 에러를 내뱉으면서도 미들웨어를 무사히 통과하는지 확인합니다.
    """
    res = await client.get("/this-is-ghost-url-1234")
    
    assert res.status_code == 404
    assert res.json()["detail"] == "Not Found"
    # 에러 상황에서도 미들웨어가 돌아서 헤더를 찍어줬는지 확인!
    assert "x-process-time" in res.headers
    print("[성공] 404 에러 정상 핸들링 및 미들웨어 통과 확인")


# ==========================================
# (선택) Prefix 라우터 연결 상태 점검
# ==========================================
async def test_router_prefixes_connected(client: AsyncClient):
    """
    main.py에서 설정한 prefix(/user, /boards, /files)들이
    정상적으로 연결되었는지 기초적인 엔드포인트를 찔러 확인합니다.
    (Method Not Allowed 등 404가 아닌 에러가 뜬다면 주소는 잘 맵핑된 것입니다)
    """
    # /user/login 은 POST 방식이므로 GET으로 찌르면 405 Method Not Allowed가 떠야 함.
    user_res = await client.get("/user/login")
    assert user_res.status_code == 405

    # /boards/allBInfo 는 GET 방식이므로 정상적으로 200 또는 404(게시물없음)가 떠야 함.
    boards_res = await client.get("/boards/allBInfo")
    assert boards_res.status_code in [200, 404]

    print("[성공] 도메인별 Prefix 라우터 정상 맵핑 확인")