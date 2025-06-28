# Book Review API

A FastAPI-based backend service for managing books and their reviews, with Redis caching and SQLite persistence.

## Features
- List all books (summary)
- Add a new book
- List reviews for a book
- Add a review for a book
- Caching with Redis for performance
- Automated tests with pytest
- Alembic migrations for schema management

## Setup Instructions

### 1. Clone the repository
```
git clone <your-repo-url>
cd book-review-api
```

### 2. Create and activate a virtual environment
```
python -m venv .venv
.venv\Scripts\activate  # On Windows
```

### 3. Install dependencies
```
pip install -r requirements.txt
```

### 4. Configure environment variables
Create a `.env` file in the project root:
```
REDIS_URL=redis://<your-redis-url>
PYTHONPATH=. pytest tests/
```

### 5. Run Alembic migrations
```
$env:PYTHONPATH = '.'; alembic upgrade head
```

### 6. Start the FastAPI server
```
uvicorn app.main:app --reload
```

Visit [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) for interactive API docs.

## API Endpoints

- `GET /books` — List all books (summary, cached)
- `POST /books` — Add a new book (invalidates cache)
- `GET /books/{id}/reviews` — List reviews for a book (cached)
- `POST /books/{id}/reviews` — Add a review for a book (invalidates cache)

## Caching Logic
- All GET endpoints use Redis for caching.
- POST endpoints invalidate the relevant cache.
- If Redis is down, the app logs a warning and continues to serve data from the database.

## Testing
- Run all tests:
```
$env:PYTHONPATH = '.'; pytest tests/
```
- Tests include unit and integration tests, including cache-miss scenarios.

## Migrations
- Alembic is used for database migrations.
- To create a new migration after model changes:
```
$env:PYTHONPATH = '.'; alembic revision --autogenerate -m "your message"
```
- To apply migrations:
```
$env:PYTHONPATH = '.'; alembic upgrade head
```
