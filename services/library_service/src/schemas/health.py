from typing import Dict
from typing import Dict, Any
from pydantic import BaseModel


class HealthResponse(BaseModel):
    service: str
    status: str
    dependencies: Dict[str, str]

    environment: str
    dependencies: Dict[str, Any]
