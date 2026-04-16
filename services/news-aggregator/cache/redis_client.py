import logging

import redis.asyncio as aioredis
from config import settings

logger = logging.getLogger(__name__)

_redis: aioredis.Redis | None = None

CACHE_INVALIDATE_CHANNEL = "channel:articles:updated"


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.redis_url, decode_responses=False)
    return _redis


async def close_redis():
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None


async def publish_cache_invalidation():
    """Notify the API gateway to flush its article cache."""
    try:
        r = await get_redis()
        await r.publish(CACHE_INVALIDATE_CHANNEL, "refresh")
        logger.debug("Published cache invalidation signal")
    except Exception as e:
        logger.warning(f"Failed to publish cache invalidation: {e}")
