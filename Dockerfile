FROM python:3.11-slim AS builder

WORKDIR /build

# Копируем только requirements для кэширования слоя
COPY requirements.txt .

# Создаем виртуальное окружение и устанавливаем зависимости воспроизводимо
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ==========================================
# ЭТАП 2: Финальный минимальный образ
# ==========================================
FROM python:3.11-slim AS final

# Создаем непривилегированного пользователя и группу (п. 3.1)
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

WORKDIR /app

# Копируем виртуальное окружение из builder (п. 3.3 - минимальный размер)
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Копируем исходный код приложения
COPY . .

# Настраиваем переменные окружения для записи только в /tmp (п. 3.5)
# При монтировании корневой ФС в Read-Only, приложение не сможет писать в /app
ENV TMPDIR=/tmp
ENV PYTHONPYCACHEPREFIX=/tmp
ENV PYTHONUNBUFFERED=1

# Передаем права на директорию приложения непривилегированному пользователю
RUN chown -R appuser:appgroup /app

# Переключаемся на непривилегированного пользователя (п. 3.1)
USER appuser

# Открываем порт (для информации, FastAPI обычно использует 8000)
EXPOSE 8000

# Команда запуска (замените app.main:app на твой реальный путь к приложению)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
