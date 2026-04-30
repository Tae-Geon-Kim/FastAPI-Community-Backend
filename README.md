# 💻 Board & User Management Backend System
회원 관리 + 게시판 + 파일 업로드 + 인증 시스템을 포함한 비동기 백엔드 API 서버

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/) 
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-05998B?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/) 
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15.0+-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org/)

---

## 📋 목차
- [프로젝트 소개](#project-intro)
- [개발 스펙 및 개발 환경](#dev-spec)
- [시작하기](#start)
- [핵심 기능](#features)
- [시스템 아키텍처](#system-architecture)
- [API](#api)
- [코드 테스트](#code_test)
- [개발 가이드](#develop-guide)

---
<a name="project-intro"></a>
## 📌 프로젝트 소개
본 프로젝트는 **회원관리 및 게시판 기능을 중심으로 한 백엔드 API**를 구현한 프로젝트입니다.  

FastAPI 기반으로 설계하여 인증, 파일 업로드, 데이터 삭제 및 복구, 테스트, 배포 자동화를 구현 / 비동기 처리 성능과 확장성, 유지보수성을 고려하였습니다.

또한, 프론트엔드와 연동하여 실제 서비스 형태로 동작하는 구조로 확장하였습니다.


### 🌐 Frontend Repository
React 기반으로 구현된 프론트엔드로 본 백엔드 API와 연동됩니다.

아래 주소를 통하여 접근 가능합니다.
- [프론트엔드 깃허브 주소](https://github.com/Tae-Geon-Kim/Community-Frontend)

### 🎯 핵심 목표 
✅ MVC 패턴 기반의 프로젝트 디렉토리 설계

✅ 데이터베이스 커넥션 풀(Connection Pool) 적용

✅ bcrypt 모듈 사용자 비밀번호 암호화 & JWT 토큰 인증 방식

✅ FastAPI 로깅 시스템을 구축하여 서버 동작 및 에러 로그 관리  

✅ 테스트 코드 작성을 통한 주요 기능 검증 및 안정성 확보  

✅ Nginx를 활용한 도메인 연결 및 배포 환경에서 API 정상 동작 검증 

✅ Docker를 활용한 컨테이너 기반 배포 환경 구축  

---
<a name="dev-spec"></a>
## ⚙️ 개발 스펙 및 개발 환경
### 🧩 Backend
- **Language**: Python 3.12.3
- **Framework**: FastAPI 0.135.1
- **Security**: Bcrypt (Password Hashing), JWT (Token Auth)

### 🗄️ Database & Storage
- **DBMS**: PostgreSQL 16.13
- **Driver**: Asyncpg 0.31.0 (Asynchronous Python driver)

### 🛠️ Tools
- **IDE**: VS Code
- **Version Control**: Git, GitHub
- **API Test**: Swagger UI, Postman

---
<a name="start"></a>
## 🚀 시작하기
### 📋 사전 요구 사항
- Python 3.12.3
- PostgreSQL 16.13
  
### 📦 의존성 관리
본 프로젝트는 **requirements.txt** 방식을 사용합니다.

#### 🧪 설치 및 실행
```text
# 1. 저장소 클론
git clone https://github.com/Tae-Geon-Kim/FastAPI-Community-Backend.git
cd FastAPI-Community-Backend

# 환경변수 설정
cp .env.example .env

# 3. Docker 컨테이너 실행 (App, DB, Nginx 모두 자동 빌드 및 실행)
docker compose up -d --build
```

#### 환경변수 (.env)
실제 환경에서는 .env 파일을 생성하여 본인의 환경에 맞게 설정해야 합니다.
```text
# .env.example

# 데이터베이스 접속 정보
DB_USER=cutshion
DB_PASSWORD=secret
DB_NAME=CommunityBackendDB
DB_HOST=127.0.0.1
DB_PORT=5432
DB_MAX_SIZE=10
DB_MIN_SIZE=5

# 폴더 경로
UPLOAD_DIR=upload

# 한 파일 최대 용량 (5MB: 5 * 1024 * 1024)
FILE_MAX_SIZE=5242880

# 게시판에 들어갈 수 있는 파일들의 최대 총 합 용량 (25MB: 25 * 1024 * 1024)
FILE_TOTAL_MAX_SIZE=26214400

# JWT 토큰 인증 정보
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30 # 30분
REFRESH_TOKEN_EXPIRE_DAYS=30 # 30일

# 로깅 정보
LOGGING_DIR=logs
FILE_NAME=server.log
WHEN=midnight
INTERVAL=1
BACKUP=7

FORMAT=%(asctime)s %(levelname)s %(message)s
DATEFMT=%m/%d/%Y %I:%M:%S %p
```
---
<a name="features"></a>
## ⚡ 핵심 기능
### 👤 User
- 회원가입 / 로그인
- JWT 기반 인증 (Access / Refresh Token)
- 사용자 정보 조회 / 수정
- Soft Delete 및 복구


### 📝 Board
- 게시글 생성 / 조회 / 수정 / 삭제
- 작성자 권한 검증
- 게시글 복구 기능

### 📁 File
- 파일 업로드 / 다운로드 / 삭제
- 파일 크기 제한 및 확장자 검증
- 게시글과 파일 연동

### 🔐 Authentication
- JWT 기반 인증 처리
- bcrypt 비밀번호 암호화
- 토큰 재발급 (Refresh Token)

### 📜 Logging
- 요청/응답 로그 기록
- 예외 및 에러 로그 기록
- 서비스 운영 및 디버깅을 위한 로그 관리

### 🧪 Testing
- pytest 기반 테스트 코드 작성
- 테스트용 DB 분리 및 롤백 처리
- API 단위 테스트 수행

### 🚀 DevOps
- Docker 기반 컨테이너 환경 구성
- GitHub Actions를 활용한 CI/CD 자동화
- Nginx 기반 리버스 프록시 구성

---
<a name="system-architecture"></a>
## 🏗️ 시스템 아키텍처
```text
Client
  ↓
Router (API Endpoint)
  ↓
Service Layer (Business Logic)
  ↓
Database (PostgreSQL / asyncpg)
```

### 🔐 JWT 인증 흐름
```text
Login → Access Token 발급 → API 요청 시 Header 포함 → 인증 검증
```

### 📊 시스템 다큐먼트
- [인증 로직 상세 (Auth Flow)](./docs/auth_flow.md)
- [사용자 관리 로직 상세 (User Flow)](./docs/user_flow.md)
- [게시판 CRUD 로직 상세 (Board Flow)](./docs/boards_flow.md)
- [파일 관리 로직 상세 (File Flow)](./docs/files_flow.md)

### 📁 프로젝트 구조 

```text
.
├── 📁 app/                      # 메인 애플리케이션 소스
│   ├── main.py                  # FastAPI 실행 엔트리 포인트
│   ├── 📁 api/                  # [Router] API 엔드포인트 정의
│   │   ├── boards.py
│   │   ├── files.py
│   │   └── user.py
│   ├── 📁 services/             # [Service] 핵심 비즈니스 로직 및 예외 처리
│   │   ├── auth.py
│   │   ├── boards.py
│   │   ├── files.py
│   │   └── user.py
│   ├── 📁 models/               # [Model] 데이터베이스 비동기 쿼리
│   │   ├── boards.py
│   │   ├── files.py
│   │   └── user.py
│   ├── 📁 schemas/              # [Schema] Pydantic 데이터 검증 및 응답 규격
│   │   ├── boards.py
│   │   ├── files.py
│   │   └── user.py
│   ├── 📁 core/                 # 공통 설정, 보안(JWT, Bcrypt) 및 로깅
│   │   ├── config.py
│   │   ├── logger.py
│   │   └── security.py
│   └── 📁 db/                   # DB 연결 및 커넥션 풀 설정
│       └── database.py
├── 📁 tests/                    # Pytest 기반 통합 및 단위 테스트
│   ├── conftest.py              
│   ├── test_boards.py
│   ├── test_files.py
│   ├── test_main.py
│   └── test_user.py
├── 📁 nginx/                    # 웹 서버 및 리버스 프록시 설정
│   └── nginx.conf
├── 📁 docs/                     # 시스템 아키텍처 및 Flow 문서화
│   ├── auth_flow.md
│   ├── boards_flow.md
│   └── user_flow.md
├── 📁 .github/                  
│   └── workflows/deploy.yml
├── docker-compose.yml           
├── Dockerfile                   
├── requirements.txt             
├── schemas.sql                  # 초기 데이터베이스 테이블 정의서
└── README.md
```

### 🗃️ 데이터베이스 스키마
### 🗄️ 테이블 구조
- [DB 테이블 구조](./docs/db_table.md)
### 💬 테이블 설명
#### - User Table
|Column|Description|Constraint|
|:--|:--|:--|
| **index** | 사용자 고유 식별 번호 | PK (NOT NULL) |
| **id** | 사용자 로그인 ID | NOT NULL, UNIQUE |
| **password** | 해싱된 비밀번호 | NOT NULL |
| **reg_date** | 회원 가입 일시 | DEFAULT NOW() |
| **update_date** | 회원 정보 수정 일시 | DEFAULT NOW() |
| **deleted_at** | 삭제된 시간 (삭제 처리) | |

#### - Boards Table
|Column|Description|Constraint|
|:--|:--|:--|
| **index** | 게시글 고유 식별 번호 | PK (NOT NULL) |
| **title** | 게시판 제목 | NOT NULL |
| **content** | 게시글 내용 | NOT NULL |
| **reg_date** | 최초 생성 일시 | DEFAULT NOW() |
| **update_date** | 최종 수정 일시 | DEFAULT NOW() |
| **user_index** | 작성자 고유 번호 (user.index 참조) | FK (NOT NULL) |
| **deleted_at** | 삭제된 시간 (삭제 처리) | |
| **total_file_size** | 해당 게시판에 있는 파일 전체 용량의 합 | DEFAULT 0 |

#### - Files Table
|Column|Description|Constraint|
|:--|:--|:--|
| **index** | 파일의 고유 식별 번호 | PK (NOT NULL) |
| **original_name** | 유저가 올린 파일 이름 | NOT NULL |
| **stored_name** | DB에 저장된 고유파일의 이름 (uuid) | NOT NULL |
| **file_path** | 파일이 저장된 실제 경로 | NOT NULL, DEFAULT |
| **file_size** | 파일 크기 (bytes) | NOT NULL |
| **reg_date** | 파일이 업로드된 일시 | DEFAULT NOW() |
| **board_index** | 소속된 게시글 번호 | FK (NOT NULL) |
| **deleted_at** | 삭제된 시간 (삭제 처리) | |

---
<a name="api"></a>
## 📡 API
### 🔌 엔드포인트 요약
아래의 링크를 통해서 API 상세 명세서를 확인하고 직접 테스트 할 수 있습니다.

Swagger UI는 프로젝트를 클론하고 docker 컨테이너를 실행한 후 (`docker compose up -d`) 링크를 통해 접속 가능합니다.

실행 환경의 포트 설정에 따라 아래 주소 중 하나로 Swagger UI에 접속 가능합니다.
- [Swagger UI (Nginx 80번 포트)](http://localhost/docs)

- [Swagger UI (FastAPI 8000번 포트)](http://localhost:8000/docs)

- [API 상세 명세서](https://www.notion.so/API-0769db8647b18277af2e813304fbddb0?source=copy_link)

#### - User API (Base URL: `/users`)
| Method | Endpoint | Description |
| :--- | :--- | :--- | 
| POST | /refresh | 만료된 JWT Access Token 재발급 |
| POST | /login | 사용자 인증 및 JWT (Access / Refresh) 토큰 발급 |
| POST | / | 신규 회원가입 (비밀번호 Bcrypt 해싱 저장) | 
| GET | /check-id/{user_id} | 신규 회원가입 전 아이디 중복 및 유효성 검사 |
| GET | /me | 로그인한 사용자 본인의 정보 조회 |
| DELETE | /me | 회원 탈퇴 처리 (soft delete) |
| PATCH | /me/id | 사용자 아이디 변경 |
| PATCH | /me/password | 사용자 비밀번호 변경 |
| POST | /me/restore | 삭제 처리된 사용자 계정 복구 |

#### - Boards API (Base URL: `/boards`)
| Method | Endpoint | Description |
| :--- | :--- | :--- | 
| POST | / | 신규 게시글 작성 |
| GET | /users/{user_id} | 특정 사용자의 게시글 목록 조회 (로그인 x / 유저 아이디 기준) |
| GET | / | 모든 사용자의 게시글 목록 전체 조회 (로그인 x) |
| PATCH | /{board_index}/title | 특정 게시글 제목 수정 |
| PATCH | /{board_index}/content | 특정 게시글 내용 수정 |
| DELETE | /{board_index} | 특정 게시글 삭제 (soft delete) |
| POST | /{board_index}/restore | 삭제 처리된 특정 게시글 복구 |

#### - Files API (Base URL: `/files`)
| Method | Endpoint | Description |
| :--- | :--- | :--- | 
| POST | /boards/{board_index} | 특정 게시글에 파일 업로드 |
| DELETE | /boards/{board_index}/{file_index} | 특정 게시글의 단일 파일 삭제 (soft delete) |
| DELETE | /boards/{board_index} | 특정 게시글에 첨부된 모든 파일 일괄 삭제 (soft delete) |
| POST | /boards/{board_index}/{file_index}/restore| 특정 게시글의 삭제 처리된 단일 파일 복구 |
| POST | /boards/{board_index}/restore | 특정 게시글의 삭제 처리된 전체 파일 일괄 복구 |
---
<a name="code_test"></a>
## 🧪 코드 테스트
### ⚙️ 테스트 도구 
- Swagger UI
- Pytest
- httpx

### ▶️ 테스트 실행 방법
이 프로젝트는 `pytest`를 기반으로 API 엔드포인트 및 비즈니스 로직 테스트를 수행합니다. 

테스트를 실행하기 전, 가상환경이 활성화되어 있는지 확인해 주세요.

- 테스트 라이브러리 설치
```text
pip install pytest pytest-asyncio httpx
```

- pytest 실행
```text
pytest tests
```

---
<a name="develop-guide"></a>
## 📘 개발가이드
### ✍️ 코드 스타일
- **주석**: 모두 한글로 작성
  
- **로그**: 영어 메시지 사용

### 📝 커밋 컨벤션
```text
feat: 새로운 기능 추가
fix: 버그 수정
docs: 문서 수정
style: 코드 포맷팅
refactor: 코드 리팩토링
test: 테스트 코드
chore: 빌드, 설정 변경
ci: CI/CD 수정
```

### 👨‍💻 Author
- Github: https://github.com/Tae-Geon-Kim
