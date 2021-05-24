from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class User(BaseModel):
    username: str


class BaseBlogPost(BaseModel):
    content: str = Field(..., min_length=1, max_length=512)


class BlogPostCreate(BaseBlogPost):
    pass


class BlogPostUpdate(BaseBlogPost):
    pass


class BlogPost(BaseBlogPost):
    id: int
    created_at: datetime
    updated_at: datetime
    likes: Optional[list[User]]
    reposts: Optional[list[User]]

    class Config:
        orm_mode = True
