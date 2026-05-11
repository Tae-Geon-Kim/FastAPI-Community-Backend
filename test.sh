# test db 자동 업데이트
#!/bin/bash
echo "테스트 DB 마이그레이션을 시작..."

# 도커 컨테이너 안에서 'DB_NAME'을 테스트 DB로 덮어씌운 상태로 Alembic 실행
# (-e 옵션을 쓰면 .env 파일을 수정하지 않아도 이 명령어 한 줄에서만 환경변수가 바뀝니다)
docker compose exec -e DB_NAME=Test_CommunityBackendDB app alembic upgrade head

echo "테스트 DB 최신화 완료. pytest를 실행합니다."

# 곧바로 pytest 실행 - 이제 pytest 실행할 떄 명령어: sh test.sh
pytest tests/