from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from services.library_service.src.models.base import Base


class Borrowing(Base):
    __tablename__ = "borrowings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True)
    borrowed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    returned_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, default="BORROWED")  # BORROWED, RETURNED

    # Relationships
    user = relationship("User", back_populates="borrowings")
    book = relationship("Book", back_populates="borrowings")

    def __repr__(self):
        return f"<Borrowing(id={self.id}, user_id={self.user_id}, book_id={self.book_id}, status='{self.status}')>"

