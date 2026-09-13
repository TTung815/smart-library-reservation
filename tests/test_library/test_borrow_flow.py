import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from services.library_service.src.models.user import User
from services.library_service.src.models.book import Book


@pytest.mark.asyncio
async def test_borrow_available_book(client: AsyncClient, db_session: AsyncSession):
    # Setup user & book với 2 cuốn còn sẵn
    user = User(name="Tester 1", email="tester1@example.com")
    book = Book(
        title="Python Concurrency",
        author="Expert",
        isbn="111-222-333",
        total_copies=2,
        available_copies=2,
    )
    db_session.add_all([user, book])
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(book)

    # Thực hiện mượn sách
    payload = {"user_id": user.id, "book_id": book.id}
    response = await client.post("/api/v1/borrow", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "BORROWED"
    assert data["borrowing_id"] is not None
    assert data["book_id"] == book.id
    assert data["user_id"] == user.id

    # Kiểm tra số lượng sách giảm còn 1
    res_book = await client.get(f"/api/v1/books/{book.id}")
    assert res_book.json()["available_copies"] == 1


@pytest.mark.asyncio
async def test_borrow_out_of_stock_triggers_reservation(client: AsyncClient, db_session: AsyncSession):
    # Setup user & book với 0 cuốn còn sẵn (đã hết sách)
    user = User(name="Tester 2", email="tester2@example.com")
    book = Book(
        title="Zero Stock Book",
        author="Expert",
        isbn="999-888-777",
        total_copies=1,
        available_copies=0,
    )
    db_session.add_all([user, book])
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(book)

    # Mượn sách khi đã hết sách
    payload = {"user_id": user.id, "book_id": book.id}
    response = await client.post("/api/v1/borrow", json=payload)

    # Phải trả về HTTP 202 Accepted và trạng thái RESERVATION_CREATED
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "RESERVATION_CREATED"
    assert data["reservation_id"] is not None
    assert data["reservation_status"] == "PENDING"
    assert data["book_id"] == book.id
    assert data["user_id"] == user.id


@pytest.mark.asyncio
async def test_borrow_user_not_found(client: AsyncClient, db_session: AsyncSession):
    book = Book(
        title="Sample Book",
        author="Author",
        isbn="555-666-777",
        total_copies=1,
        available_copies=1,
    )
    db_session.add(book)
    await db_session.commit()
    await db_session.refresh(book)

    response = await client.post("/api/v1/borrow", json={"user_id": 99999, "book_id": book.id})
    assert response.status_code == 404
    assert "User with id 99999 not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_borrow_book_not_found(client: AsyncClient, db_session: AsyncSession):
    user = User(name="Tester 3", email="tester3@example.com")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    response = await client.post("/api/v1/borrow", json={"user_id": user.id, "book_id": 99999})
    assert response.status_code == 404
    assert "Book with id 99999 not found" in response.json()["detail"]

