from typing import Dict, Any
from pydantic import BaseModel


class HealthResponse(BaseModel):
    service: str
    status: str
    environment: str
    dependencies: Dict[str, Any]
