# backend/tests/test_rate_limiter.py
import asyncio
import time
import pytest
from app.core.rate_limiter import LLMRateLimiter
from app.core.config import settings

@pytest.mark.asyncio
async def test_rate_limiter_basic():
    """Test basic rate limiting: block after limit reached"""
    limiter = LLMRateLimiter(resource_name="test_basic", limit=2, period=1)
    
    # First two should succeed immediately
    assert await limiter.acquire(wait=False) is True
    assert await limiter.acquire(wait=False) is True
    
    # Third should fail (no wait)
    assert await limiter.acquire(wait=False) is False
    
    # Check status
    is_allowed, remaining, retry_after = await limiter.check()
    assert is_allowed is False
    assert remaining == 0
    assert retry_after > 0
    
    # Wait for period to pass
    await asyncio.sleep(1.1)
    
    # Should succeed again
    assert await limiter.acquire(wait=False) is True

@pytest.mark.asyncio
async def test_rate_limiter_waiting():
    """Test that acquire(wait=True) eventually succeeds"""
    limiter = LLMRateLimiter(resource_name="test_wait", limit=1, period=1)
    
    start_time = time.time()
    
    # First call
    assert await limiter.acquire(wait=True) is True
    
    # Second call should wait approximately 1 second
    assert await limiter.acquire(wait=True) is True
    
    duration = time.time() - start_time
    print(f"Waiting duration: {duration:.4f}s")
    assert duration >= 0.95
    assert duration < 2.0

@pytest.mark.asyncio
async def test_rate_limiter_context_manager():
    """Test rate limiter as an async context manager"""
    limiter = LLMRateLimiter(resource_name="test_context", limit=1, period=1)
    
    print(f"\nTesting context manager with Redis: {limiter.redis_url}")
    
    try:
        # First entry
        async with limiter:
            pass
        
        start_time = time.time()
        # Second entry - should wait
        async with limiter:
            pass
        
        duration = time.time() - start_time
        print(f"Context manager duration: {duration:.4f}s")
        # Assert duration is close to 1.0 (allow for small jitter)
        assert duration >= 0.95, f"Expected duration >= 0.95s, got {duration:.4f}s"
    except Exception as e:
        print(f"Error in context manager test: {e}")
        raise

if __name__ == "__main__":
    import sys
    
    async def run_all():
        try:
            await test_rate_limiter_basic()
            await test_rate_limiter_waiting()
            await test_rate_limiter_context_manager()
            print("\nAll tests passed!")
        except Exception as e:
            print(f"\nTests failed: {e}")
            sys.exit(1)
            
    asyncio.run(run_all())
