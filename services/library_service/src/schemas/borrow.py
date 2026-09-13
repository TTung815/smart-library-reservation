from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class BorrowRequest(BaseModel):
    user_id: int = Field(..., gt=0, description="ID của người dùng mượn sách")
    book_id: int = Field(..., gt=0, description="ID của cuốn sách cần mượn")


class BorrowResponse(BaseModel):
    status: str = Field(..., description="'BORROWED' hoặc 'RESERVATION_CREATED'")
    message: str
    book_id: int
    user_id: int
    borrowing_id: Optional[int] = None
    reservation_id: Optional[int] = None
    reservation_status: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


    model_config = ConfigDict(from_attributes=True)
