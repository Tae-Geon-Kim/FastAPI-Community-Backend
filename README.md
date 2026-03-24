# 💻 Board & User Management Backend System
회원관리 및 게시판 관리 기능을 포함한 백엔드 시스템 구현 프로그램

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/) 
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-05998B?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/) 
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15.0+-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org/)

---

## 📋 목차
- [프로젝트 소개](#project-intro)
- [개발 스펙 및 개발 환경](#dev-spec)
- [주요 기능](#features)
- [시스템 아키텍처](#system-architecture)
- [API](#api)

---
<a name="project-intro"></a>
## 📌 프로젝트 소개
본 프로젝트는 **회원관리 및 게시판 기능을 포함한 백엔드 시스템**을 구현한 프로젝트입니다.  

사용자는 회원가입 및 로그인 후 게시글을 작성하고, 회원정보 및 게시글을 수정, 삭제할 수 있습니다.

또한 FastAPI 기반으로 설계하여 비동기 처리 성능과 확장성, 유지보수성을 고려하였습니다.

### 🎯 핵심 목표 
✅ 사용자 비밀번호를 bcrypt 모듈로 암호화하여 DB에 저장

✅ 데이터베이스 커넥션 풀(Connection Pool) 적용

✅ MVC 패턴 기반의 프로젝트 디렉토리 설계

✅ JWT 기반 토큰 인증 방식 도입

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
- **API Test**: Swagger UI (Built-in), Postman

---
<a name="features"></a>
## ✨ 주요 기능
### 👤 회원 관리
- 회원가입 / 로그인 / 로그아웃
- 비밀번호 암호화 저장 (BCrypt)
- 사용자 정보 조회, 수정, 삭제

---

### 📝 게시판 기능
- 게시글 작성 / 조회 / 수정 / 삭제 (CRUD)
- 게시글 목록 조회 (페이징 처리)

---
<a name="system-architecture"></a>
## 🏗️ 시스템 아키텍처
### 📊 시스템 다큐먼트
- [인증 로직 상세 (Auth Flow)](./docs/auth_flow.md)
- [사용자 관리 로직 상세 (User Flow)](./docs/user_flow.md)
- [게시판 CRUD 로직 상세 (Board Flow)](./docs/boards_flow.md)

### 📁 프로젝트 구조 

```text
.
├── README.md
├── 📁 app
│   ├── 📁 api
│   │   ├── boards.py
│   │   └── user.py
│   ├── 📁 core
│   │   └── security.py
│   ├── 📁 db
│   │   └── database.py
│   ├── main.py
│   ├── 📁 models
│   │   ├── boards.py
│   │   └── user.py
│   ├── 📁 schemas
│   │   ├── boards.py
│   │   └── user.py
│   └── 📁 services
│       ├── auth.py
│       ├── boards.py
│       └── user.py
├── 📁 docs
│   ├── auth_flow.md
│   ├── boards_flow.md
│   ├── db_table.md
│   └── user_flow.md
└── requirement.txt
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
| **reg_date** | 회원 가입 일시 | NOT NULL, DEFAULT |
| **update_date** | 회원 정보 수정 일시 | |

#### - Boards Table
|Column|Description|Constraint|
|:--|:--|:--|
| **index** | 게시글 고유 식별 번호 | PK (NOT NULL) |
| **title** | 게시판 제목 | NOT NULL |
| **content** | 게시글 내용 | NOT NULL |
| **reg_date** | 최초 생성 일시 | NOT NULL, DEFAULT |
| **update_date** | 최종 수정 일시 | |
| **user_index** | 작성자 고유 번호 (user.index 참조) | FK (NOT NULL) |

---
<a name="api"></a>
## 📡 API

- [API 상세 명세서]( 여기에 링크 )

- [Swagger UI]( 여기에 링크 )

| Category | Method | Endpoint | Description |
| :--- | :---: | :--- | :--- |
| **Auth** | `POST` | `/ucheck` | ID 중복 확인 및 PW 유효성 검사 |
| **User** | `POST` | `/uregister` | 신규 회원 등록 (Bcrypt 암호화) |
| **User** | `POST` | `/blogin` | 사용자 인증 및 로그인 |
| **Board** | `POST` | `/bregister` | 신규 게시글 등록 (제목 공백 검증) |
| **Board** | `POST` | `/bupdate` | 게시글 수정 및 PW 재인증 후 삭제 |


---
