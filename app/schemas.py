"""
Pydantic schemas for Book and Review models, including summary and creation schemas.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ReviewBase(BaseModel):
    """Base schema for a review."""
    reviewer: str = Field(...)
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"reviewer": "John Doe", "rating": 5, "comment": "Great book!"}
            ]
        }
    }

class ReviewCreate(ReviewBase):
    """Schema for creating a review."""
    pass

class Review(ReviewBase):
    """Schema for returning a review, including id and timestamps."""
    id: int
    created_at: datetime
    book_id: int

    model_config = {"from_attributes": True}

class BookBase(BaseModel):
    """Base schema for a book."""
    title: str = Field(...)
    author: str = Field(...)
    description: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"title": "The Great Gatsby", "author": "F. Scott Fitzgerald", "description": "A classic novel."}
            ]
        }
    }

class BookCreate(BookBase):
    """Schema for creating a book."""
    pass

class Book(BookBase):
    """Schema for returning a book, including id and reviews."""
    id: int
    reviews: List[Review] = []

    model_config = {"from_attributes": True}

class BookSummary(BaseModel):
    """Summary schema for listing books (id, title, author only)."""
    id: int
    title: str
    author: str

    model_config = {"from_attributes": True}
