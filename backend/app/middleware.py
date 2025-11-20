# backend/app/middleware.py
"""
Custom middleware for the FastAPI application
"""

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import logging
import uuid
import json
from datetime import datetime
from typing import Dict, Any, Optional
import asyncio
from collections import defaultdict, deque

from app.config import settings

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all HTTP requests and responses
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.sensitive_fields = {
            'password', 'token', 'secret', 'key', 'authorization',
            'x-api-key', 'stripe-signature'
        }
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Start time
        start_time = time.time()
        
        # Log request
        await self._log_request(request, request_id)
        
        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log error
            logger.error(
                f"Request {request_id} failed: {str(e)}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "error": str(e)
                }
            )
            # Return error response
            response = JSONResponse(
                status_code=500,
                content={"message": "Internal server error", "request_id": request_id}
            )
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Add custom headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(duration)
        
        # Log response
        await self._log_response(request, response, request_id, duration)
        
        return response
    
    async def _log_request(self, request: Request, request_id: str):
        """Log incoming request"""
        try:
            # Get request body for POST/PUT requests
            body = None
            if request.method in ["POST", "PUT", "PATCH"]:
                body = await self._get_request_body(request)
            
            log_data = {
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "headers": self._sanitize_headers(dict(request.headers)),
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
                "body": self._sanitize_body(body) if body else None
            }
            
            logger.info(f"Request {request_id} started", extra=log_data)
            
        except Exception as e:
            logger.error(f"Failed to log request: {str(e)}")
    
    async def _log_response(self, request: Request, response: Response, request_id: str, duration: float):
        """Log response"""
        try:
            log_data = {
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "status_code": response.status_code,
                "duration": duration,
                "response_size": response.headers.get("content-length")
            }
            
            if response.status_code >= 400:
                logger.warning(f"Request {request_id} completed with error", extra=log_data)
            else:
                logger.info(f"Request {request_id} completed", extra=log_data)
                
        except Exception as e:
            logger.error(f"Failed to log response: {str(e)}")
    
    async def _get_request_body(self, request: Request) -> Optional[str]:
        """Get request body safely"""
        try:
            body = await request.body()
            return body.decode('utf-8') if body else None
        except Exception:
            return None
    
    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Remove sensitive headers"""
        sanitized = {}
        for key, value in headers.items():
            if any(sensitive in key.lower() for sensitive in self.sensitive_fields):
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = value
        return sanitized
    
    def _sanitize_body(self, body: str) -> str:
        """Remove sensitive data from request body"""
        try:
            data = json.loads(body)
            if isinstance(data, dict):
                for key in list(data.keys()):
                    if any(sensitive in key.lower() for sensitive in self.sensitive_fields):
                        data[key] = "[REDACTED]"
                return json.dumps(data)
            return body
        except (json.JSONDecodeError, TypeError):
            return body


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses
    """
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Content Security Policy
        if not settings.DEBUG:
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https://api.stripe.com; "
                "frame-ancestors 'none';"
            )
            response.headers["Content-Security-Policy"] = csp
        
        # HSTS (only for HTTPS)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using sliding window algorithm
    """
    
    def __init__(self, app: ASGIApp, requests_per_minute: int = 60, burst_size: int = 10):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.client_requests = defaultdict(lambda: deque())
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()
    
    async def dispatch(self, request: Request, call_next):
        client_ip = self._get_client_ip(request)
        current_time = time.time()
        
        # Cleanup old entries periodically
        if current_time - self.last_cleanup > self.cleanup_interval:
            await self._cleanup_old_entries(current_time)
            self.last_cleanup = current_time
        
        # Check rate limit
        if await self._is_rate_limited(client_ip, current_time):
            return JSONResponse(
                status_code=429,
                content={
                    "message": "Too many requests",
                    "retry_after": 60
                },
                headers={"Retry-After": "60"}
            )
        
        # Record request
        self.client_requests[client_ip].append(current_time)
        
        return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address, considering proxy headers"""
        # Check for forwarded headers (when behind a proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    async def _is_rate_limited(self, client_ip: str, current_time: float) -> bool:
        """Check if client is rate limited"""
        requests = self.client_requests[client_ip]
        
        # Remove requests older than 1 minute
        while requests and current_time - requests[0] > 60:
            requests.popleft()
        
        # Check burst limit (requests in last 10 seconds)
        recent_requests = sum(1 for req_time in requests if current_time - req_time <= 10)
        if recent_requests >= self.burst_size:
            return True
        
        # Check per-minute limit
        return len(requests) >= self.requests_per_minute
    
    async def _cleanup_old_entries(self, current_time: float):
        """Clean up old request records"""
        for client_ip in list(self.client_requests.keys()):
            requests = self.client_requests[client_ip]
            
            # Remove requests older than 1 hour
            while requests and current_time - requests[0] > 3600:
                requests.popleft()
            
            # Remove empty deques
            if not requests:
                del self.client_requests[client_ip]


class CORSMiddleware(BaseHTTPMiddleware):
    """
    Custom CORS middleware with enhanced security
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.allowed_origins = set(settings.CORS_ORIGINS) if settings.CORS_ORIGINS else set()
        self.allowed_methods = {"GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"}
        self.allowed_headers = {
            "accept", "accept-language", "content-language", "content-type",
            "authorization", "x-requested-with", "x-api-key"
        }
    
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")
        
        # Handle preflight requests
        if request.method == "OPTIONS":
            return self._handle_preflight(request, origin)
        
        # Process request
        response = await call_next(request)
        
        # Add CORS headers
        if origin and self._is_allowed_origin(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
        
        return response
    
    def _handle_preflight(self, request: Request, origin: str) -> Response:
        """Handle CORS preflight requests"""
        headers = {}
        
        if origin and self._is_allowed_origin(origin):
            headers["Access-Control-Allow-Origin"] = origin
            headers["Access-Control-Allow-Credentials"] = "true"
            headers["Access-Control-Allow-Methods"] = ", ".join(self.allowed_methods)
            headers["Access-Control-Allow-Headers"] = ", ".join(self.allowed_headers)
            headers["Access-Control-Max-Age"] = "86400"  # 24 hours
        
        return Response(status_code=200, headers=headers)
    
    def _is_allowed_origin(self, origin: str) -> bool:
        """Check if origin is allowed"""
        if "*" in self.allowed_origins:
            return True
        return origin in self.allowed_origins


class RequestSizeMiddleware(BaseHTTPMiddleware):
    """
    Middleware to limit request body size
    """
    
    def __init__(self, app: ASGIApp, max_size: int = 50 * 1024 * 1024):  # 50MB default
        super().__init__(app)
        self.max_size = max_size
    
    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        
        if content_length:
            try:
                content_length = int(content_length)
                if content_length > self.max_size:
                    return JSONResponse(
                        status_code=413,
                        content={
                            "message": f"Request body too large. Maximum size is {self.max_size / (1024*1024):.1f}MB"
                        }
                    )
            except ValueError:
                pass
        
        return await call_next(request)


class RequestTimeoutMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle request timeouts
    """
    
    def __init__(self, app: ASGIApp, timeout: int = 30):
        super().__init__(app)
        self.timeout = timeout
    
    async def dispatch(self, request: Request, call_next):
        try:
            return await asyncio.wait_for(call_next(request), timeout=self.timeout)
        except asyncio.TimeoutError:
            return JSONResponse(
                status_code=408,
                content={"message": "Request timeout"}
            )


class HealthCheckMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle health checks without logging
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.health_paths = {"/health", "/healthz", "/ping"}
    
    async def dispatch(self, request: Request, call_next):
        # Skip detailed logging for health checks
        if request.url.path in self.health_paths:
            request.state.skip_logging = True
        
        return await call_next(request)


# Middleware for API versioning
class APIVersionMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle API versioning
    """
    
    def __init__(self, app: ASGIApp, default_version: str = "v1"):
        super().__init__(app)
        self.default_version = default_version
        self.supported_versions = {"v1"}
    
    async def dispatch(self, request: Request, call_next):
        # Extract version from URL or header
        version = self._extract_version(request)
        
        if version and version not in self.supported_versions:
            return JSONResponse(
                status_code=400,
                content={
                    "message": f"Unsupported API version: {version}",
                    "supported_versions": list(self.supported_versions)
                }
            )
        
        # Set version in request state
        request.state.api_version = version or self.default_version
        
        response = await call_next(request)
        response.headers["X-API-Version"] = request.state.api_version
        
        return response
    
    def _extract_version(self, request: Request) -> Optional[str]:
        """Extract API version from request"""
        # Check Accept header
        accept_header = request.headers.get("accept", "")
        if "application/vnd.api+json" in accept_header:
            # Extract version from accept header
            for part in accept_header.split(";"):
                if "version=" in part:
                    return part.split("version=")[1].strip()
        
        # Check custom header
        return request.headers.get("X-API-Version")


# Combined logging middleware that respects health check skipping
class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Enhanced logging middleware
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.request_logging = RequestLoggingMiddleware(app)
    
    async def dispatch(self, request: Request, call_next):
        # Check if logging should be skipped
        if getattr(request.state, 'skip_logging', False):
            return await call_next(request)
        
        return await self.request_logging.dispatch(request, call_next)