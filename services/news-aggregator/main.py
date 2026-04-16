import logging
import sys

from fastapi import FastAPI
from contextlib import asynccontextmanager

from config import settings
from db.connection import get_pool, close_pool
from cache.redis_client import get_redis, close_redis
from scheduler import start_scheduler, run_fetch_cycle
from routers import health, admin

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing database pool...")
    await get_pool()
    logger.info("Initializing Redis...")
    await get_redis()

    # Register the fetch function with the admin router
    admin.set_fetch_fn(run_fetch_cycle)

    # Start the scheduler
    start_scheduler()

    # Run an initial fetch immediately on startup
    logger.info("Running initial fetch cycle on startup...")
    await run_fetch_cycle()

    yield

    # Shutdown
    from scheduler import scheduler
    if scheduler.running:
        scheduler.shutdown(wait=False)
    await close_pool()
    await close_redis()
    logger.info("Shutdown complete")


app = FastAPI(title="Defcon News Aggregator", lifespan=lifespan)

app.include_router(health.router)
app.include_router(admin.router)
