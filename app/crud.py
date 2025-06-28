"""
CRUD operations for Book and Review models.
"""

from sqlalchemy.orm import Session
from app import models, schemas
from typing import List

def get_books(db: Session) -> List[models.Book]:
    """Return all books from the database."""
    return db.query(models.Book).all()

def create_book(db: Session, book: schemas.BookCreate) -> models.Book:
    """Create and return a new book."""
    db_book = models.Book(**book.model_dump())
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

def get_reviews_by_book_id(db: Session, book_id: int) -> List[models.Review]:
    """Return all reviews for a given book id."""
    return db.query(models.Review).filter(models.Review.book_id == book_id).all()

def create_review_for_book(db: Session, book_id: int, review: schemas.ReviewCreate) -> models.Review:
    """Create and return a new review for a book."""
    db_review = models.Review(**review.model_dump(), book_id=book_id)
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review
