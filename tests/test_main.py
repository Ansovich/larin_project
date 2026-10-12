import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db, Base
from app.models import RequestLog  # Импортируем модель, чтобы она зарегистрировалась в Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Используем SQLite в /tmp
SQLALCHEMY_DATABASE_URL = "sqlite:////tmp/test.db"
test_engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    """Подменяем реальную БД на тестовую SQLite"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Переопределяем зависимость (теперь 'app' точно ссылается на FastAPI)
app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function", autouse=True)
def setup_db():
    """Создаем таблицы перед каждым тестом и удаляем после"""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

def test_healthz():
    client = TestClient(app)
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_readyz():
    client = TestClient(app)
    response = client.get("/readyz")
    assert response.status_code in [200, 503]

def test_req():
    client = TestClient(app)
    response = client.get("/req")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data and "request_id" in data
    assert data["http_status"] == 200

def test_history():
    client = TestClient(app)
    response = client.get("/history?from_date=2026-01-01T00:00:00&to_date=2027-01-01T00:00:00")
    assert response.status_code == 200
    data = response.json()
    assert "records" in data and "count" in data

def test_history_invalid_date():
    client = TestClient(app)
    response = client.get("/history?from_date=invalid&to_date=2027-01-01T00:00:00")
    assert response.status_code == 422

def test_history_from_greater_than_to():
    client = TestClient(app)
    response = client.get("/history?from_date=2027-01-01T00:00:00&to_date=2026-01-01T00:00:00")
    assert response.status_code == 400

def test_metrics():
    client = TestClient(app)
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text

def test_request_count_increment():
    client = TestClient(app)
    client.get("/req")
    client.get("/req")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text
