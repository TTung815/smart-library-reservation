from fastapi import APIRouter, HTTPException, status
from services.reservation_service.src.schemas.reservation import ReservationDetail
from services.reservation_service.src.services.queue_service import queue_service

router = APIRouter(prefix="/reservations", tags=["Reservations"])


@router.get("/{reservation_id}", response_model=ReservationDetail)
async def get_reservation_status(reservation_id: int):
    """
    Tra cứu nhanh trạng thái đặt sách và số thứ tự hàng đợi từ Redis (In-Memory).
    """
    reservation = await queue_service.get_reservation(reservation_id=reservation_id)
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reservation {reservation_id} not found in queue",
        )
    return reservation

