"""
Custom middleware for rate limiting, logging, etc.
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
from datetime import datetime, timedelta
import time
import logging

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiting middleware
    For production, use Redis-based rate limiting
    """
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
        self.cleanup_interval = 300  # Cleanup every 5 minutes
        self.last_cleanup = time.time()
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health check and docs
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host
        
        # Get current time
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)
        
        # Clean up old requests periodically
        if time.time() - self.last_cleanup > self.cleanup_interval:
            self.cleanup_old_requests()
            self.last_cleanup = time.time()
        
        # Filter requests from last minute
        if client_ip in self.requests:
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip]
                if req_time > minute_ago
            ]
        
        # Check rate limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "retry_after": 60
                },
                headers={"Retry-After": "60"}
            )
        
        # Add current request
        self.requests[client_ip].append(now)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(
            self.requests_per_minute - len(self.requests[client_ip])
        )
        
        return response
    
    def cleanup_old_requests(self):
        """Remove old request records to prevent memory leak"""
        minute_ago = datetime.utcnow() - timedelta(minutes=1)
        
        # Remove IPs with no recent requests
        ips_to_remove = []
        for ip, requests in self.requests.items():
            valid_requests = [req for req in requests if req > minute_ago]
            if not valid_requests:
                ips_to_remove.append(ip)
            else:
                self.requests[ip] = valid_requests
        
        for ip in ips_to_remove:
            del self.requests[ip]


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Log all requests and responses
    """
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(f"Request: {request.method} {request.url.path}")
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log response
        logger.info(
            f"Response: {request.method} {request.url.path} "
            f"Status: {response.status_code} Duration: {duration:.3f}s"
        )
        
        # Add custom headers
        response.headers["X-Process-Time"] = str(duration)
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses
    """
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response
