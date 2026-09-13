from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from services.library_service.src.core.database import get_db
from services.library_service.src.schemas.book import BookCreate, BookResponse
from services.library_service.src.services.library_service import library_service

router = APIRouter(prefix="/books", tags=["Books"])


@router.get("", response_model=List[BookResponse])
async def list_books(
    skip: int = Query(0, ge=0, description="Offset số lượng bản ghi"),
    limit: int = Query(100, ge=1, le=100, description="Số lượng bản ghi tối đa"),
    db: AsyncSession = Depends(get_db),
):
    """Lấy danh sách tất cả các cuốn sách trong thư viện."""
    return await library_service.get_books(db=db, skip=skip, limit=limit)


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(
    book_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Lấy thông tin chi tiết một cuốn sách theo ID."""
    book = await library_service.get_book_by_id(db=db, book_id=book_id)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with id {book_id} not found",
        )
    return book


@router.post("", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(
    book_in: BookCreate,
    db: AsyncSession = Depends(get_db),
):
    """Thêm mới một cuốn sách vào thư viện."""
    return await library_service.create_book(db=db, book_in=book_in)

