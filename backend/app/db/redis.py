import os
import json
import logging
from typing import Any, Optional
import redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class InMemoryRedisClient:
    """In-memory Redis mock for isolated automated testing and local fallback."""

    def __init__(self):
        self._store: dict[str, str] = {}
        self._hashes: dict[str, dict[str, str]] = {}

    def ping(self) -> bool:
        return True

    def get(self, key: str) -> Optional[str]:
        return self._store.get(key)

    def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        self._store[key] = str(value)
        return True

    def delete(self, *keys: str) -> int:
        count = 0
        for k in keys:
            if k in self._store:
                del self._store[k]
                count += 1
            if k in self._hashes:
                del self._hashes[k]
                count += 1
        return count

    def hget(self, name: str, key: str) -> Optional[str]:
        return self._hashes.get(name, {}).get(str(key))

    def hgetall(self, name: str) -> dict:
        return dict(self._hashes.get(name, {}))

    def hset(self, name: str, key: str, value: str) -> int:
        if name not in self._hashes:
            self._hashes[name] = {}
        self._hashes[name][str(key)] = str(value)
        return 1

    def hdel(self, name: str, *keys: str) -> int:
        h = self._hashes.get(name, {})
        count = 0
        for k in keys:
            if str(k) in h:
                del h[str(k)]
                count += 1
        return count

    def expire(self, name: str, time: int) -> bool:
        return True

    def close(self):
        pass


class RedisManager:
    """
    Manages Redis connection lifecycle, caching operations, and health checks.
    Fails gracefully if Redis is offline without crashing the FastAPI application.
    """

    def __init__(self):
        self._client: Optional[redis.Redis] = None

    def get_client(self) -> Optional[redis.Redis]:
        """Lazy-initialize Redis client with connection pooling and socket fallback."""
        if self._client is None:
            # 1. Check for local unix domain socket if available
            unix_sock = os.getenv("REDIS_UNIX_SOCKET", "/tmp/redis.sock")
            if os.path.exists(unix_sock):
                try:
                    client = redis.Redis(
                        unix_socket_path=unix_sock,
                        password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                        decode_responses=True,
                        socket_connect_timeout=1.5,
                        socket_timeout=1.5,
                    )
                    if client.ping():
                        self._client = client
                        return self._client
                except Exception:
                    pass

            # 2. Standard TCP client
            try:
                self._client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                    db=settings.REDIS_DB,
                    decode_responses=True,
                    socket_connect_timeout=2.0,
                    socket_timeout=2.0,
                )
            except Exception as e:
                logger.warning(f"Could not initialize Redis client: {e}")
                self._client = None
        return self._client

    def ping(self) -> dict:
        """Evaluate Redis connectivity status."""
        client = self.get_client()
        if client is None:
            return {"status": "disconnected", "available": False, "detail": "Client uninitialized"}
        try:
            if client.ping():
                return {"status": "connected", "available": True, "detail": "Redis server responsive"}
            return {"status": "degraded", "available": False, "detail": "Ping did not return True"}
        except redis.ConnectionError as ce:
            logger.debug(f"Redis offline: {ce}")
            return {"status": "disconnected", "available": False, "detail": "Redis server connection refused"}
        except Exception as e:
            logger.debug(f"Redis check error: {e}")
            return {"status": "error", "available": False, "detail": str(e)}

    def get(self, key: str) -> Optional[str]:
        """Retrieve raw string value from Redis."""
        client = self.get_client()
        if not client:
            return None
        try:
            return client.get(key)
        except Exception as e:
            logger.warning(f"Redis get failed for key '{key}': {e}")
            return None

    def get_json(self, key: str) -> Optional[Any]:
        """Retrieve and deserialize JSON value from Redis."""
        raw = self.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except Exception as e:
            logger.warning(f"Redis JSON deserialization failed for key '{key}': {e}")
            return None

    def set(self, key: str, value: str, ttl_seconds: Optional[int] = None) -> bool:
        """Store string value with optional TTL."""
        client = self.get_client()
        if not client:
            return False
        try:
            ttl = ttl_seconds if ttl_seconds is not None else settings.REDIS_DEFAULT_TTL
            client.set(key, value, ex=ttl)
            return True
        except Exception as e:
            logger.warning(f"Redis set failed for key '{key}': {e}")
            return False

    def set_json(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """Serialize value to JSON and store in Redis with optional TTL."""
        try:
            serialized = json.dumps(value, default=str)
            return self.set(key, serialized, ttl_seconds=ttl_seconds)
        except Exception as e:
            logger.warning(f"Redis JSON serialization failed for key '{key}': {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key from Redis."""
        client = self.get_client()
        if not client:
            return False
        try:
            client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Redis delete failed for key '{key}': {e}")
            return False

    def close(self):
        """Close connection pool."""
        if self._client:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None


redis_client = RedisManager()
