from typing import Dict
from pydantic import BaseModel


class HealthResponse(BaseModel):
    service: str
    status: str
    dependencies: Dict[str, str]

