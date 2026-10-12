import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Получаем настройки БД из переменных окружения
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/devops_api"
)

# Создаём движок и единый Base для всех моделей
engine = create_engine(DATABASE_URL, echo=False)
Base = declarative_base()

# Создаём фабрику сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Генератор для получения сессии БД"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
