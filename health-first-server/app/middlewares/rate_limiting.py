import time
import redis
from typing import Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from app.core.config import settings
from loguru import logger


class RateLimiter:
    """Rate limiting middleware using Redis."""

    def __init__(self):
        self.redis_client = None
        self._init_redis()

    def _init_redis(self):
        """Initialize Redis connection."""
        try:
            self.redis_client = redis.from_url(settings.redis_url)
            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection established for rate limiting")
        except Exception as e:
            logger.warning(
                f"Redis connection failed: {e}. Rate limiting will be disabled."
            )
            self.redis_client = None

    def is_rate_limited(self, client_ip: str) -> bool:
        """
        Check if the client IP is rate limited.

        Args:
            client_ip (str): Client's IP address

        Returns:
            bool: True if rate limited, False otherwise
        """
        if not self.redis_client:
            return False  # Allow if Redis is not available

        try:
            key = f"rate_limit:{client_ip}"
            current_time = int(time.time())

            # Get current request count
            request_count = self.redis_client.get(key)

            if request_count is None:
                # First request, set initial count
                self.redis_client.setex(key, settings.rate_limit_window, 1)
                return False

            request_count = int(request_count)

            if request_count >= settings.rate_limit_requests:
                return True

            # Increment request count
            self.redis_client.incr(key)
            return False

        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            return False  # Allow if there's an error

    def get_remaining_requests(self, client_ip: str) -> int:
        """
        Get remaining requests for the client IP.

        Args:
            client_ip (str): Client's IP address

        Returns:
            int: Number of remaining requests
        """
        if not self.redis_client:
            return settings.rate_limit_requests

        try:
            key = f"rate_limit:{client_ip}"
            request_count = self.redis_client.get(key)

            if request_count is None:
                return settings.rate_limit_requests

            remaining = settings.rate_limit_requests - int(request_count)
            return max(0, remaining)

        except Exception as e:
            logger.error(f"Error getting remaining requests: {e}")
            return settings.rate_limit_requests

    def get_reset_time(self, client_ip: str) -> int:
        """
        Get the time when rate limit resets for the client IP.

        Args:
            client_ip (str): Client's IP address

        Returns:
            int: Unix timestamp when rate limit resets
        """
        if not self.redis_client:
            return int(time.time()) + settings.rate_limit_window

        try:
            key = f"rate_limit:{client_ip}"
            ttl = self.redis_client.ttl(key)

            if ttl == -1:  # Key exists but has no expiration
                return int(time.time()) + settings.rate_limit_window
            elif ttl == -2:  # Key doesn't exist
                return int(time.time()) + settings.rate_limit_window
            else:
                return int(time.time()) + ttl

        except Exception as e:
            logger.error(f"Error getting reset time: {e}")
            return int(time.time()) + settings.rate_limit_window


# Global rate limiter instance
rate_limiter = RateLimiter()


async def rate_limit_middleware(request: Request, call_next):
    """
    Rate limiting middleware for FastAPI.

    Args:
        request (Request): FastAPI request object
        call_next: Next middleware/endpoint function

    Returns:
        Response: FastAPI response
    """
    # Only apply rate limiting to registration endpoint
    if request.url.path == "/api/v1/provider/register" and request.method == "POST":
        client_ip = request.client.host

        # Check if rate limited
        if rate_limiter.is_rate_limited(client_ip):
            remaining_time = rate_limiter.get_reset_time(client_ip) - int(time.time())

            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "message": "Too many registration attempts. Please try again later.",
                    "error": "RATE_LIMIT_EXCEEDED",
                    "retry_after": remaining_time,
                },
                headers={
                    "Retry-After": str(remaining_time),
                    "X-RateLimit-Limit": str(settings.rate_limit_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(rate_limiter.get_reset_time(client_ip)),
                },
            )

        # Add rate limit headers to response
        response = await call_next(request)

        remaining_requests = rate_limiter.get_remaining_requests(client_ip)
        reset_time = rate_limiter.get_reset_time(client_ip)

        response.headers["X-RateLimit-Limit"] = str(settings.rate_limit_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining_requests)
        response.headers["X-RateLimit-Reset"] = str(reset_time)

        return response

    # For non-registration endpoints, just pass through
    return await call_next(request)
