#!/usr/bin/env python3
import asyncio
import time
from typing import List, Optional

class RateLimiter:
    """Rate limiter for API calls using token bucket algorithm."""
    
    def __init__(self, max_calls: int, time_window: float):
        """
        Initialize rate limiter.
        
        Args:
            max_calls: Maximum number of calls allowed in the time window
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.tokens = max_calls
        self.last_update = time.monotonic()
        self.lock = asyncio.Lock()
    
    def _add_tokens(self):
        """Add tokens based on elapsed time."""
        now = time.monotonic()
        time_passed = now - self.last_update
        new_tokens = time_passed * (self.max_calls / self.time_window)
        
        if new_tokens > 0:
            self.tokens = min(self.max_calls, self.tokens + new_tokens)
            self.last_update = now
    
    async def acquire(self):
        """
        Acquire a token, waiting if necessary.
        
        Returns when a token is available.
        """
        while True:
            async with self.lock:
                self._add_tokens()
                
                if self.tokens >= 1:
                    self.tokens -= 1
                    return
            
            # Wait and try again
            await asyncio.sleep(0.1) 