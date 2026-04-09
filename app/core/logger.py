import os
import logging
from logging.handlers import TimedRotatingFileHandler
from app.core.config import log_setting

logging_dir = log_setting.LOGGING_DIR
logging_filename = log_setting.FILE_NAME
logging_when = log_setting.WHEN
logging_interval = log_setting.INTERVAL
logging_backup = log_setting.BACKUP

logging_format = log_setting.FORMAT
logging_datefmt = log_setting.DATEFMT

os.makedirs(logging_dir, exist_ok = True)

logger = logging.getLogger("fastapi_logger")
logger.setLevel(logging.INFO)

formatter = logging.Formatter(
    fmt = logging_format,
    datefmt = logging_datefmt
)

file_handler = TimedRotatingFileHandler(
    filename = os.path.join(logging_dir, logging_filename),
    when = logging_when, 
    interval = logging_interval, # 새로운 로그 파일 갱신: logging_interval (1일) 마다
    backupCount = logging_backup # 저장기간: logging_backup (7일)
)

file_handler.setFormatter(formatter)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

if not logger.hasHandlers():
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

