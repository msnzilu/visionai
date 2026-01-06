# backend/app/core/rate_limiter.py
"""
Redis-based rate limiter for LLM API calls and other resources
"""

import time
import asyncio
import logging
from typing import Optional, Tuple
import redis.asyncio as redis
from app.core.config import settings

logger = logging.getLogger(__name__)

class LLMRateLimiter:
    """
    Redis-backed sliding window rate limiter
    """
    def __init__(
        self, 
        resource_name: str, 
        limit: int, 
        period: int,
        redis_url: Optional[str] = None
    ):
        """
        Initialize the rate limiter
        
        Args:
            resource_name: Name of the resource (e.g., 'openai_gpt4_completions')
            limit: Maximum number of requests allowed in the period
            period: Time period in seconds
            redis_url: Optional Redis URL (defaults to settings.REDIS_URL)
        """
        self.resource_name = f"rate_limit:{resource_name}"
        self.limit = limit
        self.period = period
        self.redis_url = redis_url or settings.REDIS_URL
        self._redis = None

    async def _get_redis(self):
        """Get or create Redis connection"""
        if self._redis is None:
            try:
                self._redis = redis.from_url(self.redis_url, decode_responses=True)
            except Exception as e:
                logger.error(f"Failed to connect to Redis for rate limiting: {e}")
                raise
        return self._redis

    async def check(self) -> Tuple[bool, int, float]:
        """
        Check if the request is allowed without consuming a token
        
        Returns:
            Tuple of (is_allowed, remaining, retry_after)
        """
        r = await self._get_redis()
        now = time.time()
        window_start = now - self.period
        
        key = self.resource_name
        
        try:
            # Use a pipeline to ensure atomic operations
            async with r.pipeline(transaction=True) as pipe:
                # Remove old requests outside the current window
                pipe.zremrangebyscore(key, 0, window_start)
                # Count requests in the current window
                pipe.zcard(key)
                # Get the oldest request in the window to calculate retry_after
                pipe.zrange(key, 0, 0, withscores=True)
                
                results = await pipe.execute()
                
                current_count = results[1]
                oldest_request = results[2]
                
                is_allowed = current_count < self.limit
                remaining = max(0, self.limit - current_count)
                
                retry_after = 0
                if not is_allowed and oldest_request:
                    # oldest_request is [(member, score)]
                    _, oldest_score = oldest_request[0]
                    retry_after = (oldest_score + self.period) - now
                
                return is_allowed, remaining, retry_after
                
        except Exception as e:
            logger.error(f"Error checking rate limit for {self.resource_name}: {e}")
            # Fail open if Redis is down? Or fail closed? 
            # For LLM costs, failing closed or using a local fallback might be safer.
            # Here we'll return True to avoid blocking the app, but log the error.
            return True, self.limit, 0

    async def acquire(self, wait: bool = True) -> bool:
        """
        Acquire a token from the rate limiter
        
        Args:
            wait: If True, blocks until a token is available
            
        Returns:
            bool: True if token acquired, False otherwise
        """
        r = await self._get_redis()
        
        while True:
            now = time.time()
            window_start = now - self.period
            key = self.resource_name
            
            try:
                async with r.pipeline(transaction=True) as pipe:
                    pipe.zremrangebyscore(key, 0, window_start)
                    pipe.zcard(key)
                    results = await pipe.execute()
                    
                    current_count = results[1]
                    
                    if current_count < self.limit:
                        # Add current request to the window
                        # Use uuid or similar for uniqueness if many requests happen at exact same microsecond
                        import uuid
                        member = f"{now}:{uuid.uuid4()}"
                        await r.zadd(key, {member: now})
                        # Set expiration on the key to cleanup if unused
                        await r.expire(key, self.period + 10)
                        return True
                    
                    if not wait:
                        return False
                    
                    # Wait for the oldest request to expire
                    oldest = await r.zrange(key, 0, 0, withscores=True)
                    if oldest:
                        _, oldest_score = oldest[0]
                        sleep_time = (oldest_score + self.period) - now
                        if sleep_time > 0:
                            logger.info(f"Rate limit hit for {self.resource_name}. Sleeping for {sleep_time:.2f}s")
                            await asyncio.sleep(sleep_time)
                        else:
                            # Edge case: just expired, try again immediately
                            await asyncio.sleep(0.01)
                    else:
                        # Should not happen if count > 0, but safety first
                        await asyncio.sleep(0.1)
                        
            except Exception as e:
                logger.error(f"Error acquiring rate limit for {self.resource_name}: {e}")
                return True # Fail open to prevent app crash
    
    async def __aenter__(self):
        await self.acquire(wait=True)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
