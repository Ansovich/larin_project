from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
class RequestLogCreate(BaseModel):
    """Схема для создания записи о запросе"""
    pod_name: Optional[str] = None
    node_name: Optional[str] = None
    http_status: Optional[int] = None
    request_id: Optional[str] = None
class RequestLogResponse(BaseModel):
    """Схема ответа с информацией о запросе"""
    id: int
    timestamp: datetime
    pod_name: Optional[str] = None
    node_name: Optional[str] = None
    http_status: Optional[int] = None
    request_id: Optional[str] = None
    class Config:
        from_attributes = True
class HistoryResponse(BaseModel):
    """Схема ответа для эндпоинта /history"""
    records: List[RequestLogResponse]
    count: int
