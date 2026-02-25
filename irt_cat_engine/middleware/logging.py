"""Request/Response logging middleware."""
import time
import logging
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger("irt_cat_engine.http")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all HTTP requests and responses."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response details."""
        request_id = id(request)
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request started: {request.method} {request.url.path} "
            f"[{request_id}] from {request.client.host if request.client else 'unknown'}"
        )
        
        # Log request body for POST requests (be careful with sensitive data)
        if request.method == "POST":
            # Don't log the actual body to avoid logging sensitive data
            logger.debug(f"POST request to {request.url.path} [{request_id}]")
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            # Log response
            logger.info(
                f"Request completed: {request.method} {request.url.path} "
                f"[{request_id}] status={response.status_code} duration={duration:.3f}s"
            )
            
            # Log slow requests
            if duration > 5.0:
                logger.warning(
                    f"Slow request detected: {request.method} {request.url.path} "
                    f"took {duration:.3f}s"
                )
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"[{request_id}] error={str(e)} duration={duration:.3f}s",
                exc_info=True
            )
            raise
