from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class BookBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Tiêu đề sách")
    author: str = Field(..., min_length=1, max_length=255, description="Tác giả")
    isbn: str = Field(..., min_length=5, max_length=50, description="Mã ISBN duy nhất")
    total_copies: int = Field(default=1, ge=0, description="Tổng số lượng sách")
    available_copies: int = Field(default=1, ge=0, description="Số lượng sách hiện có sẵn")


class BookCreate(BookBase):
    pass


class BookResponse(BookBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

