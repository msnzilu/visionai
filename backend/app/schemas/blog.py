# backend/app/schemas/blog.py
"""
Blog API request/response schemas
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from app.models.blog import BlogStatus, BlogAuthor, BlogSEO


class BlogPostCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    slug: Optional[str] = None  # Auto-generated if not provided
    content: str = Field(..., min_length=1)
    excerpt: Optional[str] = Field(None, max_length=500)
    
    featured_image: Optional[str] = None
    categories: List[str] = []
    tags: List[str] = []
    
    seo: Optional[BlogSEO] = None
    status: BlogStatus = BlogStatus.DRAFT
    
    @validator('slug', pre=True, always=True)
    def generate_slug(cls, v, values):
        """Auto-generate slug from title if not provided"""
        if v:
            return v
        title = values.get('title', '')
        if title:
            import re
            slug = title.lower()
            slug = re.sub(r'[^\w\s-]', '', slug)
            slug = re.sub(r'[-\s]+', '-', slug)
            return slug.strip('-')
        return None


class BlogPostUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    slug: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = Field(None, max_length=500)
    
    featured_image: Optional[str] = None
    categories: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    
    seo: Optional[BlogSEO] = None
    status: Optional[BlogStatus] = None


class BlogPostSummary(BaseModel):
    """Lightweight summary for listings"""
    id: str
    title: str
    slug: str
    excerpt: Optional[str]
    featured_image: Optional[str]
    author: BlogAuthor
    categories: List[str]
    tags: List[str]
    status: BlogStatus
    published_at: Optional[datetime]
    views: int
    reading_time: int
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BlogPostResponse(BaseModel):
    """Full blog post response"""
    id: str
    title: str
    slug: str
    content: str
    excerpt: Optional[str]
    
    author: BlogAuthor
    featured_image: Optional[str]
    
    categories: List[str]
    tags: List[str]
    
    seo: BlogSEO
    status: BlogStatus
    
    published_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    views: int
    reading_time: int
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BlogPostListResponse(BaseModel):
    """Paginated list of blog posts"""
    posts: List[BlogPostSummary]
    total: int
    page: int
    size: int
    pages: int


class CategoryResponse(BaseModel):
    name: str
    count: int


class TagResponse(BaseModel):
    name: str
    count: int


class BlogSearchRequest(BaseModel):
    query: Optional[str] = None
    categories: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    status: Optional[BlogStatus] = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=10, ge=1, le=50)
