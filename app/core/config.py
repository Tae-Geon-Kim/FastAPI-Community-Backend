import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    DB_HOST: str
    DB_PORT: int
    DB_MAX_SIZE: int = 10
    DB_MIN_SIZE: int = 5

    UPLOAD_DIR: str = "upload"

    FILE_MAX_SIZE: int = 5242880 # 5MB
    FILE_TOTAL_MAX_SIZE: int = 26214400 # 25MB
    
    model_config = SettingsConfigDict(env_file = ".env", extra = "ignore")

settings = Settings()

class JWT_Auth(BaseSettings):
    SECRET_KEY: str = "your-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    model_config = SettingsConfigDict(env_file = ".env", extra = "ignore")
    
jwt_auth = JWT_Auth()

class Logging(BaseSettings):
    LOGGING_DIR: str = "log"
    FILE_NAME: str = "app.log"
    WHEN: str = "midnight"
    INTERVAL: int = 1
    BACKUP: int = 7

    FORMAT: str = "%(asctime)s %(levelname)s %(message)s"
    DATEFMT: str =  "%m/%d/%Y %I:%M:%S %p"

    model_config = SettingsConfigDict(env_file = ".env", extra = "ignore")

log_setting = Logging()

class RedisSettings(BaseSettings):
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str | None = None
    
    model_config = SettingsConfigDict(env_file = ".env", extra = "ignore")

redis_settings = RedisSettings()