import os
import uuid
import psutil
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import text
from app.database import engine, Base, get_db, SessionLocal
from app.models import RequestLog
from app.schemas import RequestLogCreate, RequestLogResponse, HistoryResponse
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    print("✅ Таблицы в базе данных созданы или уже существуют.")
    yield
    print("🛑 Приложение останавливается.")
app = FastAPI(
    title="DevOps Test API",
    description="Простейшее API для тестового задания DevOps",
    version="1.0.0",
    lifespan=lifespan
)
@app.get("/healthz", tags=["Health"])
async def healthz():
    """
    Проверяет объем свободной памяти и загрузку процессора.
    Возвращает 200 OK, если ресурсы в норме.
    """
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    memory_available_mb = memory.available / (1024 * 1024)
    memory_percent = memory.percent
    if memory_available_mb < 100:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Недостаточно памяти: доступно {memory_available_mb:.2f} MB"
        )
    return {
        "status": "healthy",
        "cpu_percent": cpu_percent,
        "memory_available_mb": round(memory_available_mb, 2),
        "memory_percent": memory_percent
    }
@app.get("/readyz", tags=["Health"])
async def readyz():
    """
    Проверяет, может ли приложение подключиться к базе данных.
    """
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"База данных недоступна: {str(e)}"
        )
@app.get("/req", response_model=RequestLogResponse, tags=["Requests"])
async def create_request(db: SessionLocal = Depends(get_db)):
    """
    Сохраняет в БД информацию о запросе:
    - timestamp (автоматически)
    - pod_name (из переменной окружения POD_NAME)
    - node_name (из переменной окружения NODE_NAME)
    - http_status (200 для успешного запроса)
    - request_id (уникальный идентификатор)
    Возвращает текущую дату-время.
    """
    pod_name = os.getenv("POD_NAME", "local")
    node_name = os.getenv("NODE_NAME", "local")
    request_id = str(uuid.uuid4())
    request_log = RequestLog(
        pod_name=pod_name,
        node_name=node_name,
        http_status=200,
        request_id=request_id
    )
    db.add(request_log)
    db.commit()
    db.refresh(request_log)
    return request_log
@app.get("/history", response_model=HistoryResponse, tags=["Requests"])
async def get_history(
    from_date: datetime,
    to_date: datetime,
    db: SessionLocal = Depends(get_db)
):
    """
    Возвращает записи из БД за период от from_date до to_date.
    Параметры:
    - from_date: начальная дата (формат ISO 8601, например: 2026-10-12T10:00:00)
    - to_date: конечная дата (формат ISO 8601)
    Возвращает список записей и их количество.
    """
    try:
        if from_date > to_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Параметр 'from' не может быть позже параметра 'to'"
            )
        records = db.query(RequestLog).filter(
            RequestLog.timestamp >= from_date,
            RequestLog.timestamp <= to_date
        ).all()
        return {
            "records": records,
            "count": len(records)
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Неверный формат даты: {str(e)}"
        )
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'http_status']
)
REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint']
)
ERROR_5XX_COUNT = Counter(
    'http_5xx_errors_total',
    'Total number of 5xx errors'
)
class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = datetime.now()
        response = await call_next(request)
        duration = (datetime.now() - start_time).total_seconds()
        endpoint = request.url.path
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=endpoint,
            http_status=response.status_code
        ).inc()
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=endpoint
        ).observe(duration)
        if response.status_code >= 500:
            ERROR_5XX_COUNT.inc()
        return response
app.add_middleware(MetricsMiddleware)
@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """
    Возвращает основные метрики приложения в формате Prometheus:
    - Количество полученных HTTP-запросов
    - Количество ответов по статусам
    - Количество ошибок 5xx
    - Задержки при ответах
    """
    metrics_data = generate_latest()
    return Response(
        content=metrics_data,
        media_type=CONTENT_TYPE_LATEST
    )
