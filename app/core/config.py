import os
from pydantic_settings import BaseSettings, SettingsConfigDict

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
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

class JWT_Auth(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
jwt_auth = JWT_Auth()

class Logging(BaseSettings):
    LOGGING_DIR: str
    FILE_NAME: str
    WHEN: str
    INTERVAL: int
    BACKUP: int

    FORMAT: str
    DATEFMT: str
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

log_setting = Logging()