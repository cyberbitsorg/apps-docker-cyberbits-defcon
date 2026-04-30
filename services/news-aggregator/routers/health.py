from fastapi import APIRouter
from fastapi.responses import JSONResponse
from db.connection import get_pool
from cache.redis_client import get_redis

router = APIRouter()


@router.get("/health")
async def health():
    ok = True
    try:
        pool = await get_pool()
        await pool.fetchval("SELECT 1")
    except Exception:
        ok = False
    try:
        r = await get_redis()
        await r.ping()
    except Exception:
        ok = False
    return JSONResponse(
        {"status": "ok" if ok else "degraded"},
        status_code=200 if ok else 503,
    )
