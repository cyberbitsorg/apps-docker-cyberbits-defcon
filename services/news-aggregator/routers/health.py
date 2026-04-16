from fastapi import APIRouter
from db.connection import get_pool
from cache.redis_client import get_redis

router = APIRouter()


@router.get("/health")
async def health():
    status = {"status": "ok", "database": "unknown", "redis": "unknown"}
    try:
        pool = await get_pool()
        await pool.fetchval("SELECT 1")
        status["database"] = "ok"
    except Exception:
        status["database"] = "error"
        status["status"] = "degraded"

    try:
        r = await get_redis()
        await r.ping()
        status["redis"] = "ok"
    except Exception:
        status["redis"] = "error"
        status["status"] = "degraded"

    return status
