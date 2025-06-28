import os
import pytest
from unittest.mock import patch
import json
import importlib

from app.db import Base, engine

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    # Create all tables before any tests run
    Base.metadata.create_all(bind=engine)
    yield

def import_app_with_patch(mock_redis):
    # Reload app.routes.books to ensure the patch is in effect before app is imported
    import app.routes.books
    importlib.reload(app.routes.books)
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)

@pytest.fixture(scope="session", autouse=True)
def cleanup_test_data_after_tests():
    """
    Remove only test data (books and reviews with known test titles/authors) after all tests complete.
    """
    yield
    from app.db import SessionLocal
    from app.models import Book, Review
    session = SessionLocal()
    test_titles = [
        "Test Book", "Unit Test Book", "Cache Test Book", "Review Cache Book"
    ]
    # Find test books by title
    test_books = session.query(Book).filter(Book.title.in_(test_titles)).all()
    test_book_ids = [b.id for b in test_books]
    # Delete reviews for test books
    if test_book_ids:
        session.query(Review).filter(Review.book_id.in_(test_book_ids)).delete(synchronize_session=False)
    # Delete test books
    if test_book_ids:
        session.query(Book).filter(Book.id.in_(test_book_ids)).delete(synchronize_session=False)
    session.commit()
    session.close()

@pytest.fixture
def client_with_mock_redis():
    with patch("app.routes.books.db.redis_client") as mock_redis:
        client = import_app_with_patch(mock_redis)
        yield client, mock_redis

def test_create_and_get_books():
    """Test creating a book and retrieving the book list."""
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)

    response = client.get("/books")
    assert response.status_code == 200
    initial_count = len(response.json())

    new_book = {
        "title": "Test Book",
        "author": "Test Author",
        "description": "A book for testing."
    }
    response = client.post("/books", json=new_book)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == new_book["title"]

    response = client.get("/books")
    assert len(response.json()) == initial_count + 1

def test_get_books_unit():
    """Test retrieving the book list."""
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)

    response = client.get("/books")
    assert response.status_code == 200

def test_post_books_unit():
    """Test adding a new book."""
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)

    new_book = {
        "title": "Unit Test Book",
        "author": "Unit Tester",
        "description": "Unit test description."
    }
    response = client.post("/books", json=new_book)
    assert response.status_code == 201
    data = response.json()
    assert data["author"] == "Unit Tester"

def test_get_books_cache_miss_then_set(client_with_mock_redis):
    """Test cache-miss and cache-set logic for /books endpoint."""
    client, mock_redis = client_with_mock_redis

    new_book = {
        "title": "Cache Test Book",
        "author": "Cache Tester",
        "description": "Cache test description."
    }
    client.post("/books", json=new_book)

    mock_redis.get.reset_mock()
    mock_redis.set.reset_mock()
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True

    response = client.get("/books")
    assert response.status_code == 200
    books = response.json()
    assert isinstance(books, list)

    assert mock_redis.set.called
    args, kwargs = mock_redis.set.call_args
    assert args[0] == "books:all"
    json.loads(args[1])

def test_get_reviews_cache_miss_then_set(client_with_mock_redis):
    """Test cache-miss and cache-set logic for /books/{id}/reviews endpoint."""
    client, mock_redis = client_with_mock_redis

    # Create a book
    new_book = {
        "title": "Review Cache Book",
        "author": "Review Tester",
        "description": "Review cache test."
    }
    book_resp = client.post("/books", json=new_book)
    book_id = book_resp.json()["id"]

    # Add a review
    new_review = {
        "reviewer": "Cache Reviewer",
        "rating": 5,
        "comment": "Great!"
    }
    client.post(f"/books/{book_id}/reviews", json=new_review)

    mock_redis.get.reset_mock()
    mock_redis.set.reset_mock()
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True

    response = client.get(f"/books/{book_id}/reviews")
    assert response.status_code == 200
    reviews = response.json()
    assert isinstance(reviews, list)

    assert mock_redis.set.called
    args, kwargs = mock_redis.set.call_args
    assert args[0] == f"reviews:book:{book_id}"
    json.loads(args[1])

def test_error_handling_cache_down(monkeypatch):
    """Test error handling when Redis is down (raises exception)."""
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)

    def raise_redis_error(*args, **kwargs):
        raise Exception("Redis down!")

    monkeypatch.setattr("app.db.redis_client.get", raise_redis_error)
    monkeypatch.setattr("app.db.redis_client.set", raise_redis_error)
    monkeypatch.setattr("app.db.redis_client.delete", raise_redis_error)

    response = client.get("/books")
    assert response.status_code == 200
    # Should still return books from DB even if Redis is down
