from fastapi import APIRouter

from scheduler import reschedule

router = APIRouter()

_run_fetch_cycle = None


def set_fetch_fn(fn):
    global _run_fetch_cycle
    _run_fetch_cycle = fn


@router.post("/trigger")
async def trigger_refresh():
    if _run_fetch_cycle:
        await _run_fetch_cycle()
        reschedule()
    return {"triggered": True}
