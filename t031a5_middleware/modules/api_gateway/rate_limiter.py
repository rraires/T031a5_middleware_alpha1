"""Rate Limiter for API Gateway.

Implements rate limiting with multiple algorithms and storage backends.
"""

import asyncio
import logging
import time
from typing import Optional, Dict, Any, List, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict, deque
import hashlib

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse


class RateLimitAlgorithm(Enum):
    """Rate limiting algorithms."""
    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"
    LEAKY_BUCKET = "leaky_bucket"


class RateLimitScope(Enum):
    """Rate limiting scopes."""
    GLOBAL = "global"
    USER = "user"
    IP = "ip"
    API_KEY = "api_key"
    ENDPOINT = "endpoint"


@dataclass
class RateLimitRule:
    """Rate limiting rule."""
    name: str
    algorithm: RateLimitAlgorithm
    scope: RateLimitScope
    limit: int  # Number of requests
    window: int  # Time window in seconds
    burst: Optional[int] = None  # Burst limit for token bucket
    endpoints: Optional[List[str]] = None  # Specific endpoints (regex patterns)
    users: Optional[List[str]] = None  # Specific users
    ips: Optional[List[str]] = None  # Specific IPs
    priority: int = 0  # Higher priority rules are checked first
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RateLimitConfig:
    """Rate limiter configuration."""
    # Global settings
    enabled: bool = True
    default_algorithm: RateLimitAlgorithm = RateLimitAlgorithm.SLIDING_WINDOW
    
    # Default limits
    global_limit: int = 1000  # requests per minute
    user_limit: int = 100  # requests per minute
    ip_limit: int = 60  # requests per minute
    
    # Window settings
    default_window: int = 60  # seconds
    cleanup_interval: int = 300  # seconds
    
    # Storage settings
    max_entries: int = 10000
    memory_threshold: float = 0.8  # 80% memory usage threshold
    
    # Response settings
    include_headers: bool = True
    custom_response: Optional[Dict[str, Any]] = None
    
    # Rules
    rules: List[RateLimitRule] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize default rules."""
        if not self.rules:
            self.rules = [
                RateLimitRule(
                    name="global_default",
                    algorithm=self.default_algorithm,
                    scope=RateLimitScope.GLOBAL,
                    limit=self.global_limit,
                    window=self.default_window,
                    priority=0
                ),
                RateLimitRule(
                    name="user_default",
                    algorithm=self.default_algorithm,
                    scope=RateLimitScope.USER,
                    limit=self.user_limit,
                    window=self.default_window,
                    priority=1
                ),
                RateLimitRule(
                    name="ip_default",
                    algorithm=self.default_algorithm,
                    scope=RateLimitScope.IP,
                    limit=self.ip_limit,
                    window=self.default_window,
                    priority=2
                )
            ]


@dataclass
class RateLimitResult:
    """Rate limit check result."""
    allowed: bool
    rule_name: str
    limit: int
    remaining: int
    reset_time: datetime
    retry_after: Optional[int] = None  # seconds
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RateLimitStats:
    """Rate limiter statistics."""
    total_requests: int = 0
    allowed_requests: int = 0
    blocked_requests: int = 0
    rules_triggered: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    
    # Performance metrics
    avg_check_time: float = 0.0
    max_check_time: float = 0.0
    
    # Memory usage
    active_buckets: int = 0
    memory_usage: float = 0.0
    
    def get_block_rate(self) -> float:
        """Get block rate percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.blocked_requests / self.total_requests) * 100


class TokenBucket:
    """Token bucket implementation."""
    
    def __init__(self, capacity: int, refill_rate: float, burst: Optional[int] = None):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.burst = burst or capacity
        self.tokens = float(capacity)
        self.last_refill = time.time()
    
    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens.
        
        Args:
            tokens: Number of tokens to consume
        
        Returns:
            True if tokens consumed, False otherwise
        """
        now = time.time()
        
        # Refill tokens
        time_passed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + time_passed * self.refill_rate)
        self.last_refill = now
        
        # Check if we have enough tokens
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        
        return False
    
    def get_remaining(self) -> int:
        """Get remaining tokens."""
        now = time.time()
        time_passed = now - self.last_refill
        current_tokens = min(self.capacity, self.tokens + time_passed * self.refill_rate)
        return int(current_tokens)
    
    def get_reset_time(self) -> datetime:
        """Get time when bucket will be full."""
        remaining_capacity = self.capacity - self.tokens
        if remaining_capacity <= 0:
            return datetime.utcnow()
        
        seconds_to_full = remaining_capacity / self.refill_rate
        return datetime.utcnow() + timedelta(seconds=seconds_to_full)


class SlidingWindow:
    """Sliding window implementation."""
    
    def __init__(self, limit: int, window: int):
        self.limit = limit
        self.window = window  # seconds
        self.requests: deque = deque()
    
    def is_allowed(self) -> bool:
        """Check if request is allowed.
        
        Returns:
            True if allowed, False otherwise
        """
        now = time.time()
        
        # Remove old requests
        while self.requests and self.requests[0] <= now - self.window:
            self.requests.popleft()
        
        # Check limit
        if len(self.requests) < self.limit:
            self.requests.append(now)
            return True
        
        return False
    
    def get_remaining(self) -> int:
        """Get remaining requests."""
        now = time.time()
        
        # Remove old requests
        while self.requests and self.requests[0] <= now - self.window:
            self.requests.popleft()
        
        return max(0, self.limit - len(self.requests))
    
    def get_reset_time(self) -> datetime:
        """Get time when oldest request expires."""
        if not self.requests:
            return datetime.utcnow()
        
        oldest_request = self.requests[0]
        reset_time = oldest_request + self.window
        return datetime.fromtimestamp(reset_time)


class FixedWindow:
    """Fixed window implementation."""
    
    def __init__(self, limit: int, window: int):
        self.limit = limit
        self.window = window  # seconds
        self.count = 0
        self.window_start = time.time()
    
    def is_allowed(self) -> bool:
        """Check if request is allowed.
        
        Returns:
            True if allowed, False otherwise
        """
        now = time.time()
        
        # Check if we need to reset the window
        if now >= self.window_start + self.window:
            self.count = 0
            self.window_start = now
        
        # Check limit
        if self.count < self.limit:
            self.count += 1
            return True
        
        return False
    
    def get_remaining(self) -> int:
        """Get remaining requests."""
        now = time.time()
        
        # Check if we need to reset the window
        if now >= self.window_start + self.window:
            return self.limit
        
        return max(0, self.limit - self.count)
    
    def get_reset_time(self) -> datetime:
        """Get time when window resets."""
        reset_time = self.window_start + self.window
        return datetime.fromtimestamp(reset_time)


class RateLimiter:
    """Rate limiter with multiple algorithms and scopes.
    
    Implements rate limiting for API requests with configurable rules.
    """
    
    def __init__(self, config: Optional[RateLimitConfig] = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config or RateLimitConfig()
        
        # Storage for rate limit buckets
        self.buckets: Dict[str, Union[TokenBucket, SlidingWindow, FixedWindow]] = {}
        
        # Statistics
        self.stats = RateLimitStats()
        
        # Background tasks
        self._background_tasks: List[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()
        
        # Sort rules by priority (higher priority first)
        self.config.rules.sort(key=lambda r: r.priority, reverse=True)
        
        self.logger.info("Rate Limiter initialized")
    
    async def initialize(self) -> bool:
        """Initialize rate limiter.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            if self.config.enabled:
                # Start background tasks
                await self._start_background_tasks()
            
            self.logger.info("Rate Limiter initialized successfully")
            return True
        
        except Exception as e:
            self.logger.error(f"Error initializing Rate Limiter: {e}")
            return False
    
    async def _start_background_tasks(self) -> None:
        """Start background tasks."""
        # Cleanup task
        task = asyncio.create_task(self._cleanup_loop())
        self._background_tasks.append(task)
        
        # Stats update task
        task = asyncio.create_task(self._stats_update_loop())
        self._background_tasks.append(task)
    
    def _get_bucket_key(self, rule: RateLimitRule, request: Request, user_id: Optional[str] = None) -> str:
        """Generate bucket key for rule and request.
        
        Args:
            rule: Rate limit rule
            request: HTTP request
            user_id: User ID if available
        
        Returns:
            Bucket key
        """
        key_parts = [rule.name]
        
        if rule.scope == RateLimitScope.GLOBAL:
            key_parts.append("global")
        elif rule.scope == RateLimitScope.USER and user_id:
            key_parts.append(f"user:{user_id}")
        elif rule.scope == RateLimitScope.IP:
            client_ip = self._get_client_ip(request)
            key_parts.append(f"ip:{client_ip}")
        elif rule.scope == RateLimitScope.API_KEY:
            api_key = self._get_api_key(request)
            if api_key:
                key_parts.append(f"api_key:{hashlib.md5(api_key.encode()).hexdigest()[:8]}")
        elif rule.scope == RateLimitScope.ENDPOINT:
            endpoint = f"{request.method}:{request.url.path}"
            key_parts.append(f"endpoint:{endpoint}")
        
        return ":".join(key_parts)
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address.
        
        Args:
            request: HTTP request
        
        Returns:
            Client IP address
        """
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to client host
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"
    
    def _get_api_key(self, request: Request) -> Optional[str]:
        """Get API key from request.
        
        Args:
            request: HTTP request
        
        Returns:
            API key if found, None otherwise
        """
        # Check Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:]
        
        # Check X-API-Key header
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return api_key
        
        # Check query parameter
        return request.query_params.get("api_key")
    
    def _create_bucket(self, rule: RateLimitRule) -> Union[TokenBucket, SlidingWindow, FixedWindow]:
        """Create rate limit bucket for rule.
        
        Args:
            rule: Rate limit rule
        
        Returns:
            Rate limit bucket
        """
        if rule.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
            refill_rate = rule.limit / rule.window  # tokens per second
            burst = rule.burst or rule.limit
            return TokenBucket(rule.limit, refill_rate, burst)
        
        elif rule.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
            return SlidingWindow(rule.limit, rule.window)
        
        elif rule.algorithm == RateLimitAlgorithm.FIXED_WINDOW:
            return FixedWindow(rule.limit, rule.window)
        
        elif rule.algorithm == RateLimitAlgorithm.LEAKY_BUCKET:
            # Leaky bucket is similar to token bucket but with constant rate
            refill_rate = rule.limit / rule.window
            return TokenBucket(1, refill_rate)  # Capacity of 1 for constant rate
        
        else:
            # Default to sliding window
            return SlidingWindow(rule.limit, rule.window)
    
    def _rule_matches(self, rule: RateLimitRule, request: Request, user_id: Optional[str] = None) -> bool:
        """Check if rule matches request.
        
        Args:
            rule: Rate limit rule
            request: HTTP request
            user_id: User ID if available
        
        Returns:
            True if rule matches, False otherwise
        """
        if not rule.enabled:
            return False
        
        # Check endpoints
        if rule.endpoints:
            import re
            endpoint = f"{request.method}:{request.url.path}"
            if not any(re.match(pattern, endpoint) for pattern in rule.endpoints):
                return False
        
        # Check users
        if rule.users and user_id:
            if user_id not in rule.users:
                return False
        
        # Check IPs
        if rule.ips:
            client_ip = self._get_client_ip(request)
            if client_ip not in rule.ips:
                return False
        
        return True
    
    async def check_rate_limit(self, request: Request, user_id: Optional[str] = None) -> RateLimitResult:
        """Check if request is within rate limits.
        
        Args:
            request: HTTP request
            user_id: User ID if available
        
        Returns:
            Rate limit result
        """
        start_time = time.time()
        
        try:
            if not self.config.enabled:
                return RateLimitResult(
                    allowed=True,
                    rule_name="disabled",
                    limit=0,
                    remaining=0,
                    reset_time=datetime.utcnow()
                )
            
            # Check each rule in priority order
            for rule in self.config.rules:
                if not self._rule_matches(rule, request, user_id):
                    continue
                
                # Get or create bucket
                bucket_key = self._get_bucket_key(rule, request, user_id)
                
                if bucket_key not in self.buckets:
                    self.buckets[bucket_key] = self._create_bucket(rule)
                
                bucket = self.buckets[bucket_key]
                
                # Check rate limit
                if isinstance(bucket, TokenBucket):
                    allowed = bucket.consume()
                    remaining = bucket.get_remaining()
                    reset_time = bucket.get_reset_time()
                else:  # SlidingWindow or FixedWindow
                    allowed = bucket.is_allowed()
                    remaining = bucket.get_remaining()
                    reset_time = bucket.get_reset_time()
                
                # Update statistics
                self.stats.total_requests += 1
                if allowed:
                    self.stats.allowed_requests += 1
                else:
                    self.stats.blocked_requests += 1
                    self.stats.rules_triggered[rule.name] += 1
                
                # Calculate retry after
                retry_after = None
                if not allowed:
                    retry_after = int((reset_time - datetime.utcnow()).total_seconds())
                    retry_after = max(1, retry_after)  # At least 1 second
                
                result = RateLimitResult(
                    allowed=allowed,
                    rule_name=rule.name,
                    limit=rule.limit,
                    remaining=remaining,
                    reset_time=reset_time,
                    retry_after=retry_after
                )
                
                # If request is blocked, return immediately
                if not allowed:
                    return result
                
                # If this is a specific rule (not global), continue checking other rules
                if rule.scope != RateLimitScope.GLOBAL:
                    continue
            
            # If we get here, all applicable rules passed
            return RateLimitResult(
                allowed=True,
                rule_name="passed",
                limit=0,
                remaining=0,
                reset_time=datetime.utcnow()
            )
        
        except Exception as e:
            self.logger.error(f"Error checking rate limit: {e}")
            # On error, allow the request
            return RateLimitResult(
                allowed=True,
                rule_name="error",
                limit=0,
                remaining=0,
                reset_time=datetime.utcnow()
            )
        
        finally:
            # Update performance metrics
            check_time = time.time() - start_time
            self.stats.avg_check_time = (self.stats.avg_check_time + check_time) / 2
            self.stats.max_check_time = max(self.stats.max_check_time, check_time)
    
    def create_response(self, result: RateLimitResult) -> JSONResponse:
        """Create rate limit response.
        
        Args:
            result: Rate limit result
        
        Returns:
            HTTP response
        """
        headers = {}
        
        if self.config.include_headers:
            headers.update({
                "X-RateLimit-Limit": str(result.limit),
                "X-RateLimit-Remaining": str(result.remaining),
                "X-RateLimit-Reset": str(int(result.reset_time.timestamp())),
                "X-RateLimit-Rule": result.rule_name
            })
            
            if result.retry_after:
                headers["Retry-After"] = str(result.retry_after)
        
        # Use custom response if configured
        if self.config.custom_response:
            content = self.config.custom_response
        else:
            content = {
                "error": "Rate limit exceeded",
                "message": f"Too many requests. Limit: {result.limit} per {result.reset_time}",
                "retry_after": result.retry_after
            }
        
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content=content,
            headers=headers
        )
    
    async def middleware(self, request: Request, call_next, user_id: Optional[str] = None):
        """Rate limiting middleware.
        
        Args:
            request: HTTP request
            call_next: Next middleware/handler
            user_id: User ID if available
        
        Returns:
            HTTP response
        """
        # Check rate limit
        result = await self.check_rate_limit(request, user_id)
        
        if not result.allowed:
            return self.create_response(result)
        
        # Add rate limit headers to successful responses
        response = await call_next(request)
        
        if self.config.include_headers and hasattr(response, 'headers'):
            response.headers["X-RateLimit-Limit"] = str(result.limit)
            response.headers["X-RateLimit-Remaining"] = str(result.remaining)
            response.headers["X-RateLimit-Reset"] = str(int(result.reset_time.timestamp()))
            response.headers["X-RateLimit-Rule"] = result.rule_name
        
        return response
    
    def add_rule(self, rule: RateLimitRule) -> None:
        """Add rate limiting rule.
        
        Args:
            rule: Rate limit rule
        """
        self.config.rules.append(rule)
        # Re-sort rules by priority
        self.config.rules.sort(key=lambda r: r.priority, reverse=True)
        self.logger.info(f"Added rate limit rule: {rule.name}")
    
    def remove_rule(self, rule_name: str) -> bool:
        """Remove rate limiting rule.
        
        Args:
            rule_name: Name of rule to remove
        
        Returns:
            True if rule removed, False if not found
        """
        for i, rule in enumerate(self.config.rules):
            if rule.name == rule_name:
                del self.config.rules[i]
                self.logger.info(f"Removed rate limit rule: {rule_name}")
                return True
        return False
    
    def update_rule(self, rule_name: str, **kwargs) -> bool:
        """Update rate limiting rule.
        
        Args:
            rule_name: Name of rule to update
            **kwargs: Rule attributes to update
        
        Returns:
            True if rule updated, False if not found
        """
        for rule in self.config.rules:
            if rule.name == rule_name:
                for key, value in kwargs.items():
                    if hasattr(rule, key):
                        setattr(rule, key, value)
                self.logger.info(f"Updated rate limit rule: {rule_name}")
                return True
        return False
    
    def reset_bucket(self, bucket_key: str) -> bool:
        """Reset rate limit bucket.
        
        Args:
            bucket_key: Bucket key to reset
        
        Returns:
            True if bucket reset, False if not found
        """
        if bucket_key in self.buckets:
            del self.buckets[bucket_key]
            return True
        return False
    
    def reset_user_limits(self, user_id: str) -> int:
        """Reset all rate limits for user.
        
        Args:
            user_id: User ID
        
        Returns:
            Number of buckets reset
        """
        user_prefix = f"user:{user_id}"
        buckets_to_remove = [
            key for key in self.buckets.keys()
            if user_prefix in key
        ]
        
        for key in buckets_to_remove:
            del self.buckets[key]
        
        return len(buckets_to_remove)
    
    def reset_ip_limits(self, ip: str) -> int:
        """Reset all rate limits for IP.
        
        Args:
            ip: IP address
        
        Returns:
            Number of buckets reset
        """
        ip_prefix = f"ip:{ip}"
        buckets_to_remove = [
            key for key in self.buckets.keys()
            if ip_prefix in key
        ]
        
        for key in buckets_to_remove:
            del self.buckets[key]
        
        return len(buckets_to_remove)
    
    async def _cleanup_loop(self) -> None:
        """Background cleanup loop."""
        while not self._shutdown_event.is_set():
            try:
                await self.cleanup_expired_buckets()
                await asyncio.sleep(self.config.cleanup_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(60)
    
    async def _stats_update_loop(self) -> None:
        """Background stats update loop."""
        while not self._shutdown_event.is_set():
            try:
                await self.update_stats()
                await asyncio.sleep(60)  # Update every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in stats update loop: {e}")
                await asyncio.sleep(60)
    
    async def cleanup_expired_buckets(self) -> None:
        """Cleanup expired rate limit buckets."""
        try:
            current_time = time.time()
            expired_buckets = []
            
            for key, bucket in self.buckets.items():
                # Check if bucket is expired (no activity for 2x window time)
                if isinstance(bucket, (SlidingWindow, FixedWindow)):
                    # For sliding/fixed windows, check if they're empty
                    if hasattr(bucket, 'requests') and not bucket.requests:
                        expired_buckets.append(key)
                    elif hasattr(bucket, 'count') and bucket.count == 0:
                        # Check if window has expired
                        if current_time >= bucket.window_start + bucket.window * 2:
                            expired_buckets.append(key)
                elif isinstance(bucket, TokenBucket):
                    # For token buckets, check if they're full and inactive
                    if bucket.tokens >= bucket.capacity and current_time - bucket.last_refill > bucket.capacity:
                        expired_buckets.append(key)
            
            # Remove expired buckets
            for key in expired_buckets:
                del self.buckets[key]
            
            if expired_buckets:
                self.logger.debug(f"Cleaned up {len(expired_buckets)} expired buckets")
            
            # Check memory usage
            if len(self.buckets) > self.config.max_entries:
                # Remove oldest buckets
                excess_count = len(self.buckets) - self.config.max_entries
                oldest_keys = list(self.buckets.keys())[:excess_count]
                for key in oldest_keys:
                    del self.buckets[key]
                self.logger.warning(f"Removed {excess_count} buckets due to memory limit")
        
        except Exception as e:
            self.logger.error(f"Error cleaning up expired buckets: {e}")
    
    async def update_stats(self) -> None:
        """Update statistics."""
        try:
            self.stats.active_buckets = len(self.buckets)
            # Estimate memory usage (rough calculation)
            self.stats.memory_usage = len(self.buckets) * 0.001  # 1KB per bucket estimate
        
        except Exception as e:
            self.logger.error(f"Error updating stats: {e}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            'enabled': self.config.enabled,
            'total_requests': self.stats.total_requests,
            'allowed_requests': self.stats.allowed_requests,
            'blocked_requests': self.stats.blocked_requests,
            'block_rate': self.stats.get_block_rate(),
            'rules_triggered': dict(self.stats.rules_triggered),
            'active_buckets': self.stats.active_buckets,
            'memory_usage': self.stats.memory_usage,
            'avg_check_time': self.stats.avg_check_time,
            'max_check_time': self.stats.max_check_time,
            'rules_count': len(self.config.rules)
        }
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status.
        
        Returns:
            Health status dictionary
        """
        block_rate = self.stats.get_block_rate()
        memory_ok = self.stats.memory_usage < self.config.memory_threshold
        performance_ok = self.stats.avg_check_time < 0.1  # Less than 100ms
        
        return {
            'healthy': memory_ok and performance_ok and block_rate < 90,
            'block_rate': block_rate,
            'memory_usage': self.stats.memory_usage,
            'avg_check_time': self.stats.avg_check_time,
            'active_buckets': self.stats.active_buckets
        }
    
    async def shutdown(self) -> None:
        """Shutdown rate limiter."""
        try:
            self.logger.info("Shutting down Rate Limiter")
            
            # Signal shutdown
            self._shutdown_event.set()
            
            # Stop background tasks
            for task in self._background_tasks:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            self._background_tasks.clear()
            
            # Clear buckets
            self.buckets.clear()
            
            self.logger.info("Rate Limiter shutdown complete")
        
        except Exception as e:
            self.logger.error(f"Error during Rate Limiter shutdown: {e}")