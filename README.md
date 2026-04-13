# 💻 Board & User Management Backend System
회원관리 및 게시판 관리 기능을 포함한 백엔드 시스템 구현 프로그램

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/) 
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-05998B?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/) 
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15.0+-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org/)

---

## 📋 목차
- [프로젝트 소개](#project-intro)
- [개발 스펙 및 개발 환경](#dev-spec)
- [시작하기](#start)
- [주요 기능](#features)
- [시스템 아키텍처](#system-architecture)
- [API](#api)
- [개발 가이드](#develop-guide)

---
<a name="project-intro"></a>
## 📌 프로젝트 소개
본 프로젝트는 **회원관리 및 게시판 기능을 포함한 백엔드 시스템**을 구현한 프로젝트입니다.  

사용자는 회원가입 및 로그인 후 게시글을 작성하고, 회원정보 및 게시글을 수정, 삭제할 수 있습니다.

또한 FastAPI 기반으로 설계하여 비동기 처리 성능과 확장성, 유지보수성을 고려하였습니다.

### 🎯 핵심 목표 
✅ MVC 패턴 기반의 프로젝트 디렉토리 설계

✅ 데이터베이스 커넥션 풀(Connection Pool) 적용

✅ bcrypt 모듈 사용자 비밀번호 암호화 & JWT 토큰 인증 방식

✅ FastAPI 로깅 시스템을 구축하여 서버 동작 및 에러 로그 관리  

✅ 테스트 코드 작성을 통한 주요 기능 검증 및 안정성 확보  

✅ Nginx / Apache를 활용한 도메인 연결 및 배포 환경에서 API 정상 동작 검증 

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
본 프로젝트는 **requirement.txt** 방식을 사용합니다.
### 🧪 설치 및 실행

#### 가상환경 생성 및 활성화
```text
python -m venv venv
source venv/bin/activate (Windows: venv\Scripts\activate)
```
#### 패키지 설치
```text
pip install -r requirement.txt
```

#### 환경변수 설정 (.env)
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

#### 서버 실행
환경변수 설정이 끝난다면 아래 명령어를 통해 서버를 실행합니다.
```text
uvicorn app.main:app --reload
```

---
<a name="features"></a>
## ✨ 주요 기능
### 👤 회원 관리
- 회원가입 및 JWT 토큰 기반 인증
- 비밀번호 암호화 저장 (BCrypt)
- 사용자 정보 조회, 수정, 삭제
- 사용자 데이터 삭제 및 복구

---

### 📝 게시판 기능
- 게시글 작성 / 조회 / 수정 / 삭제 (CRUD)
- 게시글 목록 조회
- 게시판 삭제 및 복구

### 📤 파일 기능
- 파일 업로드 
- 파일 삭제 및 복구

---
<a name="system-architecture"></a>
## 🏗️ 시스템 아키텍처
### 📊 시스템 다큐먼트
- [인증 로직 상세 (Auth Flow)](./docs/auth_flow.md)
- [사용자 관리 로직 상세 (User Flow)](./docs/user_flow.md)
- [게시판 CRUD 로직 상세 (Board Flow)](./docs/boards_flow.md)
- [파일 관리 로직 상세 (File Flow)](./docs/files_flow.md)

### 📁 프로젝트 구조 

```text
.
├── README.md
├── 📁app
│   ├── 📁api                # 모든 Controller 경로 설정 (router)
│   │   ├── boards.py
│   │   ├── files.py
│   │   └── user.py
│   ├── 📁core                # 프로젝트 전체 설정 (비밀번호, 환경변수)
│   │   ├── config.py
│   │   ├── logger.py
│   │   └── security.py
│   ├── 📁db                    # DB 연결 및 커넥션 풀 설정
│   │   └── database.py
│   ├── main.py
│   ├── 📁models                # DB 쿼리 전용
│   │   ├── boards.py
│   │   ├── files.py
│   │   └── user.py
│   ├── 📁schemas                # 데이터 규격
│   │   ├── boards.py
│   │   ├── files.py
│   │   └── user.py
│   └── 📁services                # 비지니스 로직
│       ├── auth.py
│       ├── boards.py
│       ├── files.py
│       └── user.py
├── 📁docs                        # 설계도
│   ├── auth_flow.md
│   ├── boards_flow.md
│   ├── db_table.md
│   ├── files_flow.md
│   ├── user_flow.md
│   └── 📁imgs                    # Swaager UI 테스트 결과 이미지 (디렉토리내 이미지 파일은 생략)
├── requirement.txt
└── 📁tests                       # test fie
    ├── conftest.py
    ├── test_user.py
    ├── test_boards.py
    ├── test_files.py
    └── test_main.py
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
| **file_pathe** | 파일이 저장된 실제 경로 | NOT NULL, DEFAULT |
| **file_size** | 파일 크기 (bytes) | NOT NULL |
| **reg_date** | 파일이 업로드된 일시 | DEFAULT NOW() |
| **board_index** | 소속된 게시글 번호 | FK (NOT NULL) |
| **deleted_at** | 삭제된 시간 (삭제 처리) | |

---
<a name="api"></a>
## 📡 API
### 🔌 엔드포인트 요약
서버 실행 후 URL을 통해서 접속 가능합니다.
- [Swagger UI](http://localhost:8000/docs)

- [API 상세 명세서](https://www.notion.so/API-0769db8647b18277af2e813304fbddb0?source=copy_link)

#### - User API
| Method | Endpoint | Description |
| :--- | :---: | :--- | 
| `POST` | `/refresh` | 만료된 JWT Access Token 재발급 |
| `POST` | `/login` | 사용자 인증 및 JWT (Access / Refresh) 토큰 발급 |
| `POST` | `/uRegister`| 신규 회원가입 (비밀번호 Bcrypt 해싱 저장) | 
| `POST` | `/uCheck` | 신규 회원가입 전 아이디 중복 및 유효성 검사 |
| `POST` | `/uInfo` | 로그인한 사용자 본인의 정보 조회 |
| `POST` | `/withdraw` | 회원 탈퇴 처리 (soft delete) |
| `POST` | `/idModify` | 사용자 아이디 변경 |
| `POST` | `/pwModify` | 사용자 비밀번호 변경 |
| `POST` | `/restoreUser` | 삭제 처리된 사용자 계정 복구 |

#### - Boards API
| Method | Endpoint | Description |
| :--- | :---: | :--- | 
| `POST` | `/bRegister` | 신규 게시글 작성 |
| `GET` | `/certainBInfo` | 특정 사용자의 게시글 목록 조회 (로그인 x / 유저 이름으로) |
| `GET` | `/allBInfo` | 모든 사용자의 게시글 목록 전체 조회 (로그인 x) |
| `POST` | `/modiTitle` | 특정 게시글 제목 수정 |
| `POST` | `/modiContent` | 특정 게시글 내용 수정 |
| `POST` | `/deleteBoards` | 특정 게시글 삭제 (soft delete) |
| `POST` | `/restoreBoards` | 삭제 처리된 특정 게시글 복구 |


#### - Files API
| Method | Endpoint | Description |
| :--- | :---: | :--- | 
| `POST` | `/uploadFiles` | 특정 게시글에 파일 업로드 |
| `POST` | `/deleteFiles` | 특정 게시글의 특정 파일 하나 삭제 (soft delete) |
| `POST` | `/deleteAll` | 특정 게시글에 첨부된 모든 파일 일괄 삭제 (soft delete) |
| `POST` | `/restoreFile` | 특정 게시글의 삭제 처리된 단일 파일 복구 |
| `POST` | `/restoreAllFile` | 특정 게시글의 삭제 처리된 전체 파일 일괄 복구 |


### 🧾 Swagger 테스트 결과
#### - User API

- [User 등록 완료](./imgs/user_register_success)
- [사용자 아이디 공백 검증 실패](./imgs/user_id_fail)
- [사용자 비밀번호 공백 검증 실패](./imgs/user_pw_fail)
- [사용자 정보 조회 성공](.imgs/user_info_success)
- [사용자 아이디 변경 성공](.imgs/user_idModi_success)
- [사용자 비밀번호 변경 성공](.imgs/user_pwModi_success)
- [사용자 회원탈퇴 완료](.imgs/user_withdraw_success)
- [사용자 회원탈퇴 복구 완료](.imgs/user_restore_success)

#### - Boards API
- [게시판 등록 완료](./imgs/boards_register_success)
- [특정 유저의 게시판 조회 성공](./imgs/certain_boards_info_success)
- [모든 게시판 조회 성공](./imgs/all_boardss_info_success)
- [게시판 제목 변경 성공](./imgs/change_title_success)
- [게시판 내용 변경 성공](./imgs/change_content_success)
- [게시판 삭제 완료](./imgs/delete_boards_success)
- [게시판 복구 완료](./immgs/restore_boards_success)

#### - Files API
- [파일 등록 완료](.imgs/files_register_success)
- [단일 파일 삭제 완료](.imgs/files_delete_success)

---
<a name="develop-guide"></a>
## 👨‍💻 개발가이드
### 코드 스타일
- **주석**: 모두 한글로 작성
  
- **로그**: 영어 메시지 사용
### 테스트

### 📝 커밋 컨벤션
```text
feat: 새로운 기능 추가
fix: 버그 수정
docs: 문서 수정
style: 코드 포맷팅
refactor: 코드 리팩토링
test: 테스트 코드
chore: 빌드, 설정 변경
```
