from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from services.library_service.src.core.database import get_db
from services.library_service.src.schemas.borrow import BorrowRequest, BorrowResponse
from services.library_service.src.services.library_service import library_service

router = APIRouter(tags=["Borrowing & Reservation"])


@router.post("/borrow", response_model=BorrowResponse)
async def borrow_book(
    payload: BorrowRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint mượn sách:
    - Nếu sách còn: Trả về HTTP 200 OK với thông tin phiếu mượn (BORROWED).
    - Nếu sách hết: Trả về HTTP 202 Accepted với thông tin đặt trước (RESERVATION_CREATED)
      và kích hoạt gửi event Kafka trong background.
    """
    result = await library_service.borrow_or_reserve_book(
        db=db,
        user_id=payload.user_id,
        book_id=payload.book_id,
    )

    if result.status == "RESERVATION_CREATED":
        response.status_code = status.HTTP_202_ACCEPTED
    else:
        response.status_code = status.HTTP_200_OK

    return result

