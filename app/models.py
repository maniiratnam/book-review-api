"""
SQLAlchemy models for Book and Review, with indexing for performance.
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, func, Index
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Book(Base):
    """Book model representing a book in the database."""
    __tablename__ = 'books'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    author = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    reviews = relationship('Review', back_populates='book', cascade='all, delete-orphan')

class Review(Base):
    """Review model representing a review for a book."""
    __tablename__ = 'reviews'
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey('books.id'), nullable=False, index=True)
    reviewer = Column(String(255), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    book = relationship('Book', back_populates='reviews')

    __table_args__ = (
        Index('ix_reviews_book_id', 'book_id'),
    )
