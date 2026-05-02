import hmac

from fastapi import APIRouter, Header, HTTPException

from config import settings
from scheduler import reschedule

router = APIRouter()

_run_fetch_cycle = None


def set_fetch_fn(fn):
    global _run_fetch_cycle
    _run_fetch_cycle = fn


@router.post("/trigger")
async def trigger_refresh(x_internal_token: str = Header(default="")):
    if not settings.internal_secret or not hmac.compare_digest(x_internal_token, settings.internal_secret):
        raise HTTPException(status_code=401, detail="Unauthorized")
    if _run_fetch_cycle:
        await _run_fetch_cycle()
        reschedule()
    return {"triggered": True}
