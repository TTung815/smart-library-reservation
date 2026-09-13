from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from services.library_service.src.models.base import Base


class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="PENDING")  # PENDING, WAITING, FULFILLED, CANCELLED
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="reservations")
    book = relationship("Book", back_populates="reservations")

    def __repr__(self):
        return f"<Reservation(id={self.id}, user_id={self.user_id}, book_id={self.book_id}, status='{self.status}')>"

