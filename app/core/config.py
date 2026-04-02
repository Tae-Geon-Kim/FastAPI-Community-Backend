import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    DB_HOST: str
    DB_PORT: int
    DB_MAX_SIZE: int
    DB_MIN_SIZE: int

    UPLOAD_DIR: str

    FILE_MAX_SIZE: int
    FILE_TOTAL_MAX_SIZE: int

    class Config:
        env_file = ".env"

settings = Settings()
