from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app import schemas, crud
import app.db as db
import json
import logging

logger = logging.getLogger("book_review_api")

router = APIRouter()

def get_db():
    """Dependency to get a SQLAlchemy session."""
    db_session = db.SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()

@router.get(
    "/books",
    response_model=List[schemas.BookSummary],
    description="Get a summary list of all books (id, title, author). Uses Redis cache for performance."
)
def read_books(db_session: Session = Depends(get_db)):
    """Fetch all books (summary only), using Redis cache if available."""
    cache_key = "books:all"
    try:
        cached = db.redis_client.get(cache_key)
        if cached:
            logger.info("Cache hit for books:all")
            return [schemas.BookSummary.model_validate(book) for book in json.loads(cached)]
    except Exception as e:
        logger.warning(f"REDIS GET ERROR: {e}")
        cached = None

    books = crud.get_books(db_session)
    try:
        logger.info("Setting cache for books:all")
        db.redis_client.set(
            cache_key,
            json.dumps([
                schemas.BookSummary.model_validate(book).model_dump() for book in books
            ]),
            ex=300
        )
    except Exception as e:
        logger.warning(f"REDIS SET ERROR: {e}")

    return [schemas.BookSummary.model_validate(book) for book in books]

@router.post(
    "/books",
    response_model=schemas.Book,
    status_code=201,
    description="Add a new book and invalidate the books cache."
)
def create_book(book: schemas.BookCreate, db_session: Session = Depends(get_db)):
    """Create a new book and clear the books cache."""
    created_book = crud.create_book(db_session, book)
    try:
        db.redis_client.delete("books:all")
        logger.info("Cleared books:all cache after POST /books")
    except Exception as e:
        logger.warning(f"REDIS DELETE ERROR: {e}")
    return created_book

@router.get(
    "/books/{id}/reviews",
    response_model=List[schemas.Review],
    description="Get all reviews for a book by id. Uses Redis cache for performance."
)
def get_reviews(id: int, db_session: Session = Depends(get_db)):
    """Fetch all reviews for a book, using Redis cache if available."""
    cache_key = f"reviews:book:{id}"
    try:
        cached = db.redis_client.get(cache_key)
        if cached:
            logger.info(f"Cache hit for {cache_key}")
            return [schemas.Review.model_validate(review) for review in json.loads(cached)]
    except Exception as e:
        logger.warning(f"REDIS GET ERROR: {e}")
        cached = None

    reviews = crud.get_reviews_by_book_id(db_session, id)
    try:
        logger.info(f"Setting cache for {cache_key}")
        db.redis_client.set(
            cache_key,
            json.dumps([
                schemas.Review.model_validate(review).model_dump() for review in reviews
            ], default=str),
            ex=300
        )
    except Exception as e:
        logger.warning(f"REDIS SET ERROR: {e}")

    if reviews is None:
        raise HTTPException(status_code=404, detail="Book not found or no reviews.")
    return reviews

@router.post(
    "/books/{id}/reviews",
    response_model=schemas.Review,
    status_code=201,
    description="Add a review for a book and invalidate the reviews cache for that book."
)
def create_review(id: int, review: schemas.ReviewCreate, db_session: Session = Depends(get_db)):
    """Create a review for a book and clear the reviews cache for that book."""
    created_review = crud.create_review_for_book(db_session, id, review)
    cache_key = f"reviews:book:{id}"
    try:
        db.redis_client.delete(cache_key)
        logger.info(f"Cleared {cache_key} cache after POST /books/{id}/reviews")
    except Exception as e:
        logger.warning(f"REDIS DELETE ERROR: {e}")
    return created_review
