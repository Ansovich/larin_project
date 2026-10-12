#!/bin/sh
set -e
echo "🚀 Запуск приложения..."
echo "⏳ Ожидание готовности PostgreSQL..."
until python3 -c "
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/devops_api')
engine = create_engine(DATABASE_URL)
try:
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))
    print('✅ PostgreSQL готов!')
except OperationalError:
    print(' PostgreSQL ещё не готов...')
    exit(1)
"; do
    sleep 2
done
echo " Создание таблиц в базе данных..."
python3 -c "
from app.database import engine, Base
from app.models import RequestLog
Base.metadata.create_all(bind=engine)
print('✅ Таблицы созданы или уже существуют!')
"
echo " Запуск FastAPI приложения..."
exec "$@"
