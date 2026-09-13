import asyncio
from sqlalchemy import select
from services.library_service.src.core.database import AsyncSessionLocal, engine
from services.library_service.src.core.logging import logger
from services.library_service.src.models.base import Base
from services.library_service.src.models.user import User
from services.library_service.src.models.book import Book


async def seed_data():
    logger.info("Initializing database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Seed Users
        users_to_seed = [
            {"id": 1, "name": "Nguyen Van A", "email": "vana@example.com"},
            {"id": 2, "name": "Tran Thi B", "email": "thib@example.com"},
            {"id": 3, "name": "Le Van C", "email": "vanc@example.com"},
        ]

        for u in users_to_seed:
            existing = await session.execute(select(User).where(User.email == u["email"]))
            if not existing.scalar_one_or_none():
                user = User(name=u["name"], email=u["email"])
                session.add(user)
                logger.info(f"Seeding user: {u['name']} ({u['email']})")

        # 2. Seed Books
        books_to_seed = [
            {
                "title": "Designing Data-Intensive Applications",
                "author": "Martin Kleppmann",
                "isbn": "978-1449373320",
                "total_copies": 3,
                "available_copies": 3,
            },
            {
                "title": "Clean Architecture",
                "author": "Robert C. Martin",
                "isbn": "978-0134494166",
                "total_copies": 1,
                "available_copies": 1,  # Chỉ còn 1 cuốn để test mượn hết và tranh chấp
            },
            {
                "title": "The Pragmatic Programmer",
                "author": "David Thomas, Andrew Hunt",
                "isbn": "978-0135957059",
                "total_copies": 1,
                "available_copies": 0,  # Đã hết sẵn để demo reservation flow ngay lập tức
            },
        ]

        for b in books_to_seed:
            existing = await session.execute(select(Book).where(Book.isbn == b["isbn"]))
            if not existing.scalar_one_or_none():
                book = Book(
                    title=b["title"],
                    author=b["author"],
                    isbn=b["isbn"],
                    total_copies=b["total_copies"],
                    available_copies=b["available_copies"],
                )
                session.add(book)
                logger.info(f"Seeding book: '{b['title']}' (available: {b['available_copies']}/{b['total_copies']})")

        await session.commit()
        logger.info("Database seeding completed successfully!")


if __name__ == "__main__":
    asyncio.run(seed_data())

