"""
Redis connection manager for caching and pub/sub.

Provides:
- Redis cache connection (hot data)
- Redis pub/sub connection (events)
- Connection pooling and error handling
"""

import os
import json
import redis
from typing import Optional, Any, Dict, List
import logging

logger = logging.getLogger(__name__)

# Redis connection pools (created on first use)
_cache_pool: Optional[redis.ConnectionPool] = None
_pubsub_pool: Optional[redis.ConnectionPool] = None
_redis_available: Optional[bool] = None  # Circuit breaker: None=Unknown, True=Available, False=Unavailable


def get_redis_url(service: str = "cache") -> str:
    """
    Get Redis URL from environment or use defaults.
    
    Args:
        service: "cache" or "pubsub" (can use same Redis instance or separate)
        
    Returns:
        Redis URL string
    """
    # Support separate Redis instances for cache and pub/sub
    if service == "pubsub":
        url = os.environ.get("REDIS_PUBSUB_URL") or os.environ.get("REDIS_URL")
    else:
        url = os.environ.get("REDIS_URL")
    
    # Default to localhost if not set
    if not url:
        host = os.environ.get("REDIS_HOST", "localhost")
        port = int(os.environ.get("REDIS_PORT", 6379))
        db = 0 if service == "cache" else 1  # Use different DBs if same instance
        url = f"redis://{host}:{port}/{db}"
    
    return url


def get_cache_connection() -> Optional[redis.Redis]:
    """
    Get Redis connection for caching (hot data).
    
    Returns:
        Redis client instance, or None if Redis is unavailable
    """
    global _cache_pool, _redis_available
    
    # Circuit breaker check
    if _redis_available is False:
        return None
    
    try:
        if _cache_pool is None:
            url = get_redis_url("cache")
            _cache_pool = redis.ConnectionPool.from_url(
                url,
                max_connections=50,
                decode_responses=True,
                socket_connect_timeout=2,  # Shorter timeout for non-blocking
                socket_timeout=2,  # Shorter timeout for non-blocking
                retry_on_timeout=False,  # Don't retry to avoid blocking
                health_check_interval=30,
            )
            logger.info(f"Created Redis cache pool: {url}")
        
        client = redis.Redis(connection_pool=_cache_pool)
        
        # Verify connection on first use
        if _redis_available is None:
            try:
                client.ping()
                _redis_available = True
                logger.info("Redis connection verified successfully")
            except Exception as e:
                _redis_available = False
                logger.warning(f"Redis connection failed ({e}), disabling Redis cache")
                return None
                
        return client
    except Exception as e:
        logger.debug(f"Redis cache connection unavailable: {e}")
        _redis_available = False
        return None


def get_pubsub_connection() -> Optional[redis.Redis]:
    """
    Get Redis connection for pub/sub (events).
    
    Returns:
        Redis client instance, or None if unavailable
    """
    global _pubsub_pool, _redis_available
    
    # Circuit breaker check
    if _redis_available is False:
        return None
    
    try:
        if _pubsub_pool is None:
            url = get_redis_url("pubsub")
            _pubsub_pool = redis.ConnectionPool.from_url(
                url,
                max_connections=50,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
            )
            logger.info(f"Created Redis pub/sub pool: {url}")
        
        return redis.Redis(connection_pool=_pubsub_pool)
    except Exception as e:
        logger.debug(f"Redis pub/sub connection unavailable: {e}")
        return None


def test_redis_connection() -> bool:
    """
    Test Redis connectivity.
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        cache = get_cache_connection()
        cache.ping()
        return True
    except Exception as e:
        logger.error(f"Redis connection test failed: {e}")
        return False


# Cache key prefixes
class CacheKeys:
    """Centralized cache key naming."""
    
    @staticmethod
    def player_state(username: str) -> str:
        return f"player:{username}:state"
    
    @staticmethod
    def player_location(username: str) -> str:
        return f"player:{username}:location"
    
    @staticmethod
    def player_session(username: str) -> str:
        return f"player:{username}:session"
    
    @staticmethod
    def room_state(room_id: str) -> str:
        return f"room:{room_id}:state"
    
    @staticmethod
    def room_players(room_id: str) -> str:
        return f"room:{room_id}:players"
    
    @staticmethod
    def room_events(room_id: str) -> str:
        return f"room:{room_id}:events"
    
    @staticmethod
    def global_world_time() -> str:
        return "global:world_time"
    
    @staticmethod
    def global_weather() -> str:
        return "global:weather"
    
    @staticmethod
    def global_active_players() -> str:
        return "global:active_players"


# Cache helpers
def get_cached_state(key: str, default: Any = None) -> Optional[Any]:
    """
    Get cached state from Redis.
    
    Args:
        key: Cache key
        default: Default value if not found
        
    Returns:
        Cached value or default
    """
    try:
        cache = get_cache_connection()
        if cache is None:
            return default
            
        value = cache.get(key)
        if value:
            return json.loads(value)
        return default
    except Exception as e:
        logger.error(f"Error getting cached state {key}: {e}")
        return default


def set_cached_state(key: str, value: Any, ttl: int = 900) -> bool:
    """
    Set cached state in Redis.
    
    Args:
        key: Cache key
        value: Value to cache (must be JSON serializable)
        ttl: Time to live in seconds (default 15 minutes)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        cache = get_cache_connection()
        if cache is None:
            return False
            
        cache.setex(key, ttl, json.dumps(value))
        return True
    except Exception as e:
        logger.error(f"Error setting cached state {key}: {e}")
        return False


def delete_cached_state(key: str) -> bool:
    """Delete cached state."""
    try:
        cache = get_cache_connection()
        if cache is None:
            return False
            
        cache.delete(key)
        return True
    except Exception as e:
        logger.error(f"Error deleting cached state {key}: {e}")
        return False

