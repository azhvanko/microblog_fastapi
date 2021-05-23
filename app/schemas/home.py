from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class BlogPostUser(BaseModel):
    id: int
    username: str


class HomeBlogPost(BaseModel):
    post_id: int
    content: str
    created_at: datetime
    user: BlogPostUser
    author: Optional[BlogPostUser]
    likes_count: Optional[int]
    reposts_count: Optional[int]
