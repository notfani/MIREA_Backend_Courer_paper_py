import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/messenger")

# Создаем engine с настройками пула и retry
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Проверяет соединение перед использованием
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,  # Переподключаемся каждый час
    echo=False
)

# Пытаемся подключиться с retry
max_retries = 5
retry_delay = 2

for attempt in range(max_retries):
    try:
        # Проверяем подключение
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Successfully connected to database")
        break
    except Exception as e:
        if attempt < max_retries - 1:
            logger.warning(f"Database connection attempt {attempt + 1} failed: {e}")
            logger.info(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
        else:
            logger.error(f"Failed to connect to database after {max_retries} attempts")
            raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()