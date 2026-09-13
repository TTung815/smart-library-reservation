from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict


class ReservationDetail(BaseModel):
    reservation_id: int = Field(..., description="ID của lượt đặt chỗ")
    user_id: int = Field(..., description="ID của người dùng")
    book_id: int = Field(..., description="ID cuốn sách đặt chỗ")
    status: str = Field(default="WAITING", description="Trạng thái: WAITING, PROCESSED, CANCELLED")
    position: int = Field(..., ge=1, description="Vị trí hiện tại trong hàng đợi (bắt đầu từ 1)")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(from_attributes=True)

