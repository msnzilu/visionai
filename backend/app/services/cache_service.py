# backend/app/services/cache_service.py
"""
Redis cache service for performance optimization
"""

import json
import redis.asyncio as redis
from typing import Optional, Any, Callable
import logging
import asyncio
from app.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Redis-based caching service"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("Connected to Redis cache")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            self.redis_client = None
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Disconnected from Redis")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.redis_client:
            return None
        
        try:
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.error(f"Cache get error for {key}: {e}")
        
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL"""
        if not self.redis_client:
            return False
        
        try:
            serialized = json.dumps(value, default=str)
            await self.redis_client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Cache set error for {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.redis_client:
            return False
        
        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error for {key}: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        if not self.redis_client:
            return 0
        
        try:
            keys = []
            async for key in self.redis_client.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                deleted = await self.redis_client.delete(*keys)
                logger.info(f"Cleared {deleted} keys matching {pattern}")
                return deleted
        except Exception as e:
            logger.error(f"Cache clear pattern error: {e}")
        
        return 0
    
    async def get_or_set(
        self,
        key: str,
        func: Callable,
        ttl: int = 3600
    ) -> Any:
        """Get from cache or execute function and cache result"""
        
        cached = await self.get(key)
        if cached is not None:
            return cached
        
        result = await func() if asyncio.iscoroutinefunction(func) else func()
        
        await self.set(key, result, ttl)
        
        return result


cache_service = CacheService()


async def init_cache():
    """Initialize cache on startup"""
    await cache_service.connect()


async def close_cache():
    """Close cache on shutdown"""
    await cache_service.disconnect()