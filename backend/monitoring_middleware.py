"""
Monitoring middleware for automatic metrics collection.

This middleware automatically tracks:
- Request counts
- Response times
- Error rates
- Endpoint usage
"""

import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .monitoring import metrics_collector


class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically collect request metrics."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        """Process request and collect metrics."""
        # Record start time
        start_time = time.time()
        
        # Get request details
        method = request.method
        path = request.url.path
        
        # Process request
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            # Record error
            latency_ms = (time.time() - start_time) * 1000
            metrics_collector.record_request(path, method, 500, latency_ms)
            raise
        
        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000
        
        # Record metrics
        metrics_collector.record_request(path, method, status_code, latency_ms)
        
        # Add custom headers for monitoring
        response.headers["X-Response-Time"] = f"{latency_ms:.2f}ms"
        
        return response

