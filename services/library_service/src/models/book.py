from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from services.library_service.src.models.base import Base


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False, index=True)
    author = Column(String(255), nullable=False)
    isbn = Column(String(50), unique=True, nullable=False, index=True)
    total_copies = Column(Integer, nullable=False, default=1)
    available_copies = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    borrowings = relationship("Borrowing", back_populates="book", cascade="all, delete-orphan")
    reservations = relationship("Reservation", back_populates="book", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Book(id={self.id}, title='{self.title}', available={self.available_copies}/{self.total_copies})>"

