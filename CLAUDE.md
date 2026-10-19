# FastAPI Community Backend

## Stack

- Python 3.12
- FastAPI
- PostgreSQL 16
- asyncpg
- Redis
- Alembic
- pytest / pytest-asyncio
- Docker

## Architecture

- `app/api/`: HTTP routing and dependency injection
- `app/services/`: business logic
- `app/models/`: database queries
- `app/db/`: database and Redis connection infrastructure
- `app/schemas/`: request/response schemas
- `app/core/`: shared configuration, security, logging

## Development rules

- Keep database queries in `app/models/`.
- Use asyncpg parameter binding (`$1`, `$2`, ...) for SQL values.
- Do not construct SQL using f-strings, string concatenation, or `.format()`.
- Do not introduce blocking I/O into async request paths.
- Production code should use logging instead of `print()`.
- Database schema changes must include an Alembic migration.
- Do not modify `main` directly. Work on a branch and use pull requests.

## Verification

Run relevant tests after changes.

Full test suite:

```bash
pytest tests/
```

Database migrations:

```bash
alembic upgrade head
```

## Working style

- Investigate existing behavior before changing code.
- Prefer the smallest change that solves the problem.
- Preserve the existing architecture unless there is a justified reason to change it.
- Add or update tests for behavior changes.