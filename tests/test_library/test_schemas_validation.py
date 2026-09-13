import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from services.library_service.src.models.book import Book


@pytest.mark.asyncio
async def test_create_book_duplicate_isbn(client: AsyncClient, db_session: AsyncSession):
    # Tạo sẵn 1 cuốn sách
    book = Book(
        title="Existing Book",
        author="Author",
        isbn="DUPLICATE-ISBN-123",
        total_copies=1,
        available_copies=1,
    )
    db_session.add(book)
    await db_session.commit()

    # Cố tình tạo sách thứ 2 có cùng ISBN
    payload = {
        "title": "Another Book",
        "author": "Another Author",
        "isbn": "DUPLICATE-ISBN-123",
        "total_copies": 2,
        "available_copies": 2,
    }
    response = await client.post("/api/v1/books", json=payload)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_book_invalid_payload(client: AsyncClient):
    # Payload thiếu title và isbn
    invalid_payload = {
        "author": "Only Author",
        "total_copies": -5,  # Số âm không hợp lệ
    }
    response = await client.post("/api/v1/books", json=invalid_payload)
    assert response.status_code == 422  # Pydantic validation error


@pytest.mark.asyncio
async def test_borrow_invalid_payload(client: AsyncClient):
    # user_id và book_id không hợp lệ (số âm)
    response = await client.post("/api/v1/borrow", json={"user_id": -1, "book_id": 0})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Library Service"
    assert data["status"] == "running"
