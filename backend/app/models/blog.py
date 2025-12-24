# backend/app/models/blog.py
"""
Blog-related Pydantic models
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum


class BlogStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class BlogAuthor(BaseModel):
    user_id: str
    name: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None


class BlogSEO(BaseModel):
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    keywords: List[str] = []
    og_image: Optional[str] = None  # Open Graph image for social sharing
    og_title: Optional[str] = None
    og_description: Optional[str] = None


class BlogPost(BaseModel):
    id: Optional[str] = Field(alias="_id")
    title: str = Field(..., min_length=1, max_length=200)
    slug: str = Field(..., min_length=1, max_length=250)
    content: str = Field(..., min_length=1)  # Full blog content (HTML or Markdown)
    excerpt: Optional[str] = Field(None, max_length=500)  # Short summary
    
    author: Optional[BlogAuthor] = None  # Made optional to handle legacy/malformed data
    featured_image: Optional[str] = None  # URL to header image
    
    categories: List[str] = []  # ["AI", "Career Tips", "Job Search"]
    tags: List[str] = []  # ["resume", "automation", "CV"]
    
    seo: BlogSEO = Field(default_factory=BlogSEO)
    
    status: BlogStatus = BlogStatus.DRAFT
    
    published_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    views: int = 0  # Track popularity
    reading_time: int = 0  # Estimated minutes
    
    # For sitemap
    priority: float = Field(default=0.5, ge=0.0, le=1.0)
    change_frequency: str = "weekly"  # always, hourly, daily, weekly, monthly, yearly, never
    
    @validator('slug')
    def validate_slug(cls, v):
        """Ensure slug is URL-friendly"""
        import re
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug must contain only lowercase letters, numbers, and hyphens')
        return v
    
    @validator('reading_time', pre=True, always=True)
    def calculate_reading_time(cls, v, values):
        """Calculate reading time based on content (avg 200 words/min)"""
        if v and v > 0:
            return v
        content = values.get('content', '')
        if content:
            word_count = len(content.split())
            return max(1, round(word_count / 200))
        return 1
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
