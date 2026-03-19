#기본 틀 : 작동하는지만 확인 
import asyncpg
import asyncio

DATABASE_URL = "postgresql://cutshion:cutshion%40@127.0.0.1:5432/CommunityBackendDB"

async def connect_db():
    print("DB 연결 시도")
    conn = await asyncpg.connect(DATABASE_URL)

    try:
        now = await conn.fetchval('SELECT NOW()')
        print(f"연결 성공. DB 현재 시간: {now}")

    except Exception as e:
        print(f"작업 중 에러 발생: {e}")

    finally:
        await conn.close()
        print("DB 연결이 닫혔습니다.")

if __name__ == "__main__":
    asyncio.run(connect_db())
