from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from services.library_service.src.models.book import Book
from services.library_service.src.models.user import User
from services.library_service.src.models.borrowing import Borrowing
from services.library_service.src.models.reservation import Reservation
from services.library_service.src.schemas.book import BookCreate
from services.library_service.src.schemas.borrow import BorrowResponse
from services.library_service.src.kafka.producer import kafka_producer
from services.library_service.src.core.logging import logger


class LibraryBusinessService:
    @staticmethod
    async def get_books(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Book]:
        stmt = select(Book).offset(skip).limit(limit).order_by(Book.id.asc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_book_by_id(db: AsyncSession, book_id: int) -> Optional[Book]:
        stmt = select(Book).where(Book.id == book_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_book(db: AsyncSession, book_in: BookCreate) -> Book:
        # Kiểm tra ISBN đã tồn tại chưa
        stmt = select(Book).where(Book.isbn == book_in.isbn)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Book with ISBN '{book_in.isbn}' already exists"
            )

        book = Book(
            title=book_in.title,
            author=book_in.author,
            isbn=book_in.isbn,
            total_copies=book_in.total_copies,
            available_copies=book_in.available_copies,
        )
        db.add(book)
        await db.commit()
        await db.refresh(book)
        logger.info(f"Created new book: id={book.id}, title='{book.title}', copies={book.available_copies}")
        return book

    @staticmethod
    async def borrow_or_reserve_book(db: AsyncSession, user_id: int, book_id: int) -> BorrowResponse:
        """
        Nghiệp vụ mượn sách kết hợp xử lý tranh chấp (Concurrency) bằng Row-Level Locking (Pessimistic Lock):
        1. Kiểm tra User tồn tại.
        2. Khóa dòng sách được chọn bằng SELECT ... FOR UPDATE để tránh race condition khi nhiều user cùng mượn.
        3. Nếu còn sách (available_copies > 0):
           - Giảm available_copies đi 1
           - Tạo bản ghi Borrowing (status='BORROWED')
           - Trả về status 'BORROWED'
        4. Nếu hết sách (available_copies <= 0):
           - Tạo bản ghi Reservation (status='PENDING')
           - Bắn Kafka event 'BookReservationRequested'
           - Trả về status 'RESERVATION_CREATED'
        """
        # 1. Kiểm tra User
        user_stmt = select(User).where(User.id == user_id)
        user_res = await db.execute(user_stmt)
        user = user_res.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found"
            )

        # 2. Khóa dòng Book với FOR UPDATE
        # with_for_update() sinh ra 'SELECT ... FOR UPDATE' trong PostgreSQL
        book_stmt = select(Book).where(Book.id == book_id).with_for_update()
        book_res = await db.execute(book_stmt)
        book = book_res.scalar_one_or_none()

        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Book with id {book_id} not found"
            )

        # 3. Luồng Sách Còn: Synchronous Borrowing
        if book.available_copies > 0:
            book.available_copies -= 1
            borrowing = Borrowing(
                user_id=user.id,
                book_id=book.id,
                status="BORROWED",
            )
            db.add(borrowing)
            await db.commit()
            await db.refresh(borrowing)

            logger.info(
                f"[BorrowSuccess] User {user.id} borrowed '{book.title}'. "
                f"Remaining copies: {book.available_copies}/{book.total_copies}. BorrowingID: {borrowing.id}"
            )

            return BorrowResponse(
                status="BORROWED",
                message=f"Book '{book.title}' borrowed successfully.",
                book_id=book.id,
                user_id=user.id,
                borrowing_id=borrowing.id,
            )

        # 4. Luồng Sách Hết: Asynchronous Reservation Creation
        else:
            reservation = Reservation(
                user_id=user.id,
                book_id=book.id,
                status="PENDING",
            )
            db.add(reservation)
            await db.commit()
            await db.refresh(reservation)

            logger.info(
                f"[OutOfStock] Book '{book.title}' is out of stock. "
                f"Created reservation id={reservation.id} (PENDING) for user {user.id}."
            )

            # Bắn event sang Kafka topic bất đồng bộ
            await kafka_producer.publish_reservation_requested(
                reservation_id=reservation.id,
                user_id=user.id,
                book_id=book.id,
            )

            return BorrowResponse(
                status="RESERVATION_CREATED",
                message=f"Book '{book.title}' is currently out of stock. Reservation created and queued.",
                book_id=book.id,
                user_id=user.id,
                reservation_id=reservation.id,
                reservation_status="PENDING",
            )


library_service = LibraryBusinessService()

