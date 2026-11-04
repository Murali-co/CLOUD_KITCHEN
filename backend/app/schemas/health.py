from typing import Dict, Any
from pydantic import BaseModel


class ServiceStatus(BaseModel):
    status: str
    available: bool
    detail: str


class HealthResponse(BaseModel):
    api_status: str
    version: str
    environment: str
    mysql: ServiceStatus
    redis: ServiceStatus
