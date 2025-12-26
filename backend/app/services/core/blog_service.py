# backend/app/services/blog_service.py
"""
Blog service layer - Business logic for blog operations
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import re
from app.models.blog import BlogPost, BlogStatus, BlogAuthor, BlogSEO
from app.schemas.blog import (
    BlogPostCreate, 
    BlogPostUpdate, 
    BlogPostResponse,
    BlogPostSummary,
    BlogPostListResponse,
    CategoryResponse,
    TagResponse
)


class BlogService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.blog_posts
    
    async def ensure_indexes(self):
        """Create database indexes for performance"""
        await self.collection.create_index("slug", unique=True)
        await self.collection.create_index([("status", 1), ("published_at", -1)])
        await self.collection.create_index("categories")
        await self.collection.create_index("tags")
        await self.collection.create_index([("title", "text"), ("content", "text"), ("excerpt", "text")])
        await self.collection.create_index([("views", -1)]) # Improved sorting performance
    
    def _generate_unique_slug(self, base_slug: str, existing_slugs: List[str]) -> str:
        """Generate a unique slug by appending numbers if needed"""
        if base_slug not in existing_slugs:
            return base_slug
        
        counter = 1
        while f"{base_slug}-{counter}" in existing_slugs:
            counter += 1
        return f"{base_slug}-{counter}"
    
    async def create_post(self, post_data: BlogPostCreate, author: BlogAuthor) -> BlogPostResponse:
        """Create a new blog post"""
        # Generate slug if not provided
        slug = post_data.slug
        if not slug:
            slug = self._slugify(post_data.title)
        
        # Ensure slug is unique
        existing = await self.collection.find_one({"slug": slug})
        if existing:
            # Find all similar slugs
            similar_slugs = []
            async for doc in self.collection.find({"slug": {"$regex": f"^{slug}"}}):
                similar_slugs.append(doc["slug"])
            slug = self._generate_unique_slug(slug, similar_slugs)
        
        # Calculate reading time
        word_count = len(post_data.content.split())
        reading_time = max(1, round(word_count / 200))
        
        # Prepare blog post document
        post_dict = {
            "title": post_data.title,
            "slug": slug,
            "content": post_data.content,
            "excerpt": post_data.excerpt or self._generate_excerpt(post_data.content),
            "author": author.dict(),
            "featured_image": post_data.featured_image,
            "categories": post_data.categories,
            "tags": post_data.tags,
            "seo": (post_data.seo or BlogSEO()).dict(),
            "status": post_data.status,
            "published_at": datetime.utcnow() if post_data.status == BlogStatus.PUBLISHED else None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "views": 0,
            "reading_time": reading_time,
            "priority": 0.7 if post_data.status == BlogStatus.PUBLISHED else 0.3,
            "change_frequency": "weekly"
        }
        
        result = await self.collection.insert_one(post_dict)
        post_dict["_id"] = str(result.inserted_id)
        
        return BlogPostResponse(id=post_dict["_id"], **{k: v for k, v in post_dict.items() if k != "_id"})
    
    async def get_post_by_slug(self, slug: str, increment_views: bool = False) -> Optional[BlogPostResponse]:
        """Get a blog post by slug"""
        post = await self.collection.find_one({"slug": slug})
        if not post:
            return None
        
        # Increment view count
        if increment_views:
            await self.collection.update_one(
                {"_id": post["_id"]},
                {"$inc": {"views": 1}}
            )
            post["views"] = post.get("views", 0) + 1
        
        post["id"] = str(post["_id"])
        return BlogPostResponse(**{k: v for k, v in post.items() if k != "_id"})
    
    async def get_post_by_id(self, post_id: str) -> Optional[BlogPostResponse]:
        """Get a blog post by ID"""
        try:
            post = await self.collection.find_one({"_id": ObjectId(post_id)})
        except:
            return None
        
        if not post:
            return None
        
        post["id"] = str(post["_id"])
        return BlogPostResponse(**{k: v for k, v in post.items() if k != "_id"})
    
    async def update_post(self, post_id: str, update_data: BlogPostUpdate) -> Optional[BlogPostResponse]:
        """Update a blog post"""
        update_dict = update_data.dict(exclude_unset=True)
        
        if not update_dict:
            return await self.get_post_by_id(post_id)
        
        # Handle status change to published
        if update_dict.get("status") == BlogStatus.PUBLISHED:
            existing = await self.collection.find_one({"_id": ObjectId(post_id)})
            if existing and existing.get("status") != BlogStatus.PUBLISHED:
                update_dict["published_at"] = datetime.utcnow()
        
        # Recalculate reading time if content changed
        if "content" in update_dict:
            word_count = len(update_dict["content"].split())
            update_dict["reading_time"] = max(1, round(word_count / 200))
        
        update_dict["updated_at"] = datetime.utcnow()
        
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(post_id)},
                {"$set": update_dict}
            )
            
            if result.modified_count == 0:
                return None
            
            return await self.get_post_by_id(post_id)
        except:
            return None
    
    async def delete_post(self, post_id: str) -> bool:
        """Delete a blog post"""
        try:
            result = await self.collection.delete_one({"_id": ObjectId(post_id)})
            return result.deleted_count > 0
        except:
            return False
    
    async def list_posts(
        self,
        page: int = 1,
        size: int = 10,
        status: Optional[BlogStatus] = None,
        categories: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        sort_by: str = "published_at" 
    ) -> BlogPostListResponse:
        """List blog posts with filtering and pagination"""
        query = {}
        
        # Filter by status
        if status:
            query["status"] = status.value
        
        # Filter by categories
        if categories:
            query["categories"] = {"$in": categories}
        
        # Filter by tags
        if tags:
            query["tags"] = {"$in": tags}
        
        # Search in title, content, excerpt
        if search_query:
            query["$text"] = {"$search": search_query}
        
        # Count total
        total = await self.collection.count_documents(query)
        
        # Calculate pagination
        skip = (page - 1) * size
        pages = (total + size - 1) // size
        
        # Determine sort field
        sort_field = "published_at"
        if sort_by == "views":
            sort_field = "views"
        elif sort_by == "created_at":
             sort_field = "created_at"
             
        # Fetch posts
        cursor = self.collection.find(query).sort(sort_field, -1).skip(skip).limit(size)
        
        posts = []
        async for post in cursor:
            post["id"] = str(post["_id"])
            try:
                posts.append(BlogPostSummary(**{k: v for k, v in post.items() if k != "_id"}))
            except Exception as e:
                # Log error but skip valid post to prevent 400/500 for entire list
                print(f"Skipping malformed post {post.get('_id')}: {e}")
                continue
        
        return BlogPostListResponse(
            posts=posts,
            total=total,
            page=page,
            size=size,
            pages=pages
        )
    
    async def get_categories(self) -> List[CategoryResponse]:
        """Get all categories with post counts"""
        pipeline = [
            {"$match": {"status": BlogStatus.PUBLISHED.value}},
            {"$unwind": "$categories"},
            {"$group": {"_id": "$categories", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        categories = []
        async for cat in self.collection.aggregate(pipeline):
            categories.append(CategoryResponse(name=cat["_id"], count=cat["count"]))
        
        return categories
    
    async def get_tags(self) -> List[TagResponse]:
        """Get all tags with post counts"""
        pipeline = [
            {"$match": {"status": BlogStatus.PUBLISHED.value}},
            {"$unwind": "$tags"},
            {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        tags = []
        async for tag in self.collection.aggregate(pipeline):
            tags.append(TagResponse(name=tag["_id"], count=tag["count"]))
        
        return tags
    
    async def get_related_posts(self, post_id: str, limit: int = 3) -> List[BlogPostSummary]:
        """Get related posts based on tags and categories"""
        post = await self.collection.find_one({"_id": ObjectId(post_id)})
        if not post:
            return []
        
        # Find posts with similar tags or categories
        query = {
            "_id": {"$ne": ObjectId(post_id)},
            "status": BlogStatus.PUBLISHED.value,
            "$or": [
                {"tags": {"$in": post.get("tags", [])}},
                {"categories": {"$in": post.get("categories", [])}}
            ]
        }
        
        cursor = self.collection.find(query).limit(limit)
        
        related = []
        async for related_post in cursor:
            related_post["id"] = str(related_post["_id"])
            related.append(BlogPostSummary(**{k: v for k, v in related_post.items() if k != "_id"}))
        
        return related
    
    def _slugify(self, text: str) -> str:
        """Convert text to URL-friendly slug"""
        text = text.lower()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[-\s]+', '-', text)
        return text.strip('-')
    
    def _generate_excerpt(self, content: str, max_length: int = 200) -> str:
        """Generate excerpt from content"""
        # Remove HTML tags
        clean_content = re.sub(r'<[^>]+>', '', content)
        
        if len(clean_content) <= max_length:
            return clean_content
        
        # Truncate at word boundary
        excerpt = clean_content[:max_length].rsplit(' ', 1)[0]
        return excerpt + "..."

    async def get_blog_stats(self) -> Dict[str, Any]:
        """
        Get blog statistics (counts by status, views, etc.)
        """
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_posts": {"$sum": 1},
                    "total_views": {"$sum": "$views"},
                    "published_count": {
                        "$sum": {
                            "$cond": [{"$eq": ["$status", BlogStatus.PUBLISHED.value]}, 1, 0]
                        }
                    },
                    "draft_count": {
                        "$sum": {
                            "$cond": [{"$eq": ["$status", BlogStatus.DRAFT.value]}, 1, 0]
                        }
                    },
                    "archived_count": {
                        "$sum": {
                            "$cond": [{"$eq": ["$status", BlogStatus.ARCHIVED.value]}, 1, 0]
                        }
                    }
                }
            }
        ]

        result = await self.collection.aggregate(pipeline).to_list(1)
        
        if not result:
            return {
                "total_posts": 0,
                "total_views": 0,
                "published_count": 0,
                "draft_count": 0,
                "archived_count": 0
            }
            
        return {k: v for k, v in result[0].items() if k != "_id"}
