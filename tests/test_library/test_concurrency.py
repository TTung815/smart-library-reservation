import asyncio
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from services.library_service.src.models.user import User
from services.library_service.src.models.book import Book


@pytest.mark.asyncio
async def test_concurrency_single_copy_depletion(client: AsyncClient, db_session: AsyncSession):
    # Cuốn sách chỉ có 1 bản duy nhất
    book = Book(
        title="Rare Manuscript",
        author="Historian",
        isbn="000-111-222",
        total_copies=1,
        available_copies=1,
    )
    user1 = User(name="User First", email="first@example.com")
    user2 = User(name="User Second", email="second@example.com")

    db_session.add_all([book, user1, user2])
    await db_session.commit()
    await db_session.refresh(book)
    await db_session.refresh(user1)
    await db_session.refresh(user2)

    # User 1 mượn cuốn sách
    res1 = await client.post("/api/v1/borrow", json={"user_id": user1.id, "book_id": book.id})
    # User 2 mượn ngay sau đó khi sách vừa hết
    res2 = await client.post("/api/v1/borrow", json={"user_id": user2.id, "book_id": book.id})

    # User 1 thành công mượn sách
    assert res1.status_code == 200
    assert res1.json()["status"] == "BORROWED"
    assert res1.json()["borrowing_id"] is not None

    # User 2 tự động chuyển thành đặt trước (Reservation) vì sách đã hết
    assert res2.status_code == 202
    assert res2.json()["status"] == "RESERVATION_CREATED"
    assert res2.json()["reservation_id"] is not None
    assert res2.json()["reservation_status"] == "PENDING"

    # Kiểm tra số lượng sách không bao giờ bị âm
    res_book = await client.get(f"/api/v1/books/{book.id}")
    assert res_book.json()["available_copies"] == 0

