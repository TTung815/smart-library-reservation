import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Library Service"
    assert data["status"] in ("healthy", "ok")
    assert data["dependencies"]["database"]["status"] == "connected"
    assert "latency_ms" in data["dependencies"]["database"]
    assert "x-request-id" in response.headers




@pytest.mark.asyncio
async def test_create_and_get_book(client: AsyncClient):
    payload = {
        "title": "Clean Code",
        "author": "Robert C. Martin",
        "isbn": "978-0132350884",
        "total_copies": 5,
        "available_copies": 5,
    }
    # 1. Tạo sách mới
    res_create = await client.post("/api/v1/books", json=payload)
    assert res_create.status_code == 201
    created_book = res_create.json()
    assert created_book["title"] == payload["title"]
    assert created_book["available_copies"] == 5
    book_id = created_book["id"]

    # 2. Lấy chi tiết sách theo ID
    res_get = await client.get(f"/api/v1/books/{book_id}")
    assert res_get.status_code == 200
    book_data = res_get.json()
    assert book_data["id"] == book_id
    assert book_data["isbn"] == payload["isbn"]

    # 3. Liệt kê danh sách sách
    res_list = await client.get("/api/v1/books")
    assert res_list.status_code == 200
    books = res_list.json()
    assert len(books) >= 1
    assert any(b["id"] == book_id for b in books)


@pytest.mark.asyncio
async def test_get_non_existent_book(client: AsyncClient):
    response = await client.get("/api/v1/books/99999")
    assert response.status_code == 404

