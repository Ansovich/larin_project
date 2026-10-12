from sqlalchemy import Column, Integer, String, DateTime, func
from app.database import Base

class RequestLog(Base):
    """Модель для хранения информации о запросах в PostgreSQL"""
    __tablename__ = "request_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    pod_name = Column(String(255), nullable=True)
    node_name = Column(String(255), nullable=True)
    http_status = Column(Integer, nullable=True)
    request_id = Column(String(255), nullable=True)
