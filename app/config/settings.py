from dotenv import load_dotenv
from fastapi import FastAPI 
from loguru import logger
import os
from .init_db import init_db

load_dotenv()
app = FastAPI()



LOG_DIR = os.getenv("LOG_DIR", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logger.add(
    f"{LOG_DIR}/activity.log", 
    rotation="10 MB", 
    level="DEBUG"
)


logger.add(
    f"{LOG_DIR}/error.log", 
    rotation="10 MB", 
    level="ERROR"
)

logger.info(f"LOG_DIR: {LOG_DIR}")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
logger.info(f"LINE_CHANNEL_ACCESS_TOKEN: {LINE_CHANNEL_ACCESS_TOKEN}")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
logger.info(f"LINE_CHANNEL_SECRET: {LINE_CHANNEL_SECRET}")
OLLAMA_HOST = os.getenv("OLLAMA_HOST")
logger.info(f"OLLAMA_HOST: {OLLAMA_HOST}")
OLLAMA_PORT = os.getenv("OLLAMA_PORT")
logger.info(f"OLLAMA_PORT: {OLLAMA_PORT}")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")
logger.info(f"OLLAMA_MODEL: {OLLAMA_MODEL}")

DB_DIR = os.getenv("DB_DIR", "db")
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.getenv("DB_PATH", f"{DB_DIR}/finance.db")
init_db(DB_PATH)
logger.info("SQLite 資料庫與 records 表格已準備就緒")