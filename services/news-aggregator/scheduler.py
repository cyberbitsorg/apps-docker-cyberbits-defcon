import logging
from datetime import datetime, timezone, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import settings
from db.connection import get_pool
from db.articles import upsert_article, upsert_dedup_log, trim_old_articles, get_recent_articles, get_new_article_count_since
from db.defcon import insert_defcon_history
from cache.redis_client import get_redis, publish_cache_invalidation
from pipeline.deduplicator import is_duplicate, fingerprint as make_fingerprint, _token_set, _jaccard, _temporal_conflict, JACCARD_THRESHOLD
from pipeline.normalizer import normalize
from pipeline.scorer import compute_global_score
from feeds.bleeping_computer import BleepingComputerFeed
from feeds.dark_reading import DarkReadingFeed
from feeds.help_net_security import HelpNetSecurityFeed
from feeds.security_week import SecurityWeekFeed
from feeds.the_hacker_news import TheHackerNewsFeed

logger = logging.getLogger(__name__)

FEEDS = [
    BleepingComputerFeed(),
    DarkReadingFeed(),
    HelpNetSecurityFeed(),
    SecurityWeekFeed(),
    TheHackerNewsFeed(),
]

scheduler = AsyncIOScheduler()


def _within_batch_duplicate(title: str, seen_titles: list[str]) -> bool:
    """Check if title is a duplicate of anything already accepted in this batch."""
    if not seen_titles:
        return False
    new_tokens = _token_set(title)
    for existing in seen_titles:
        if _temporal_conflict(title, existing):
            continue
        j = _jaccard(new_tokens, _token_set(existing))
        if j >= JACCARD_THRESHOLD:
            logger.info(f"[Dedup batch] Jaccard={j:.2f}: '{title[:60]}' ≈ '{existing[:60]}'")
            return True
    return False


async def run_fetch_cycle():
    logger.info("Starting fetch cycle...")
    pool = await get_pool()
    redis = await get_redis()

    # --- Step 1: collect all raw articles from all feeds ---
    all_raw = []
    for feed in FEEDS:
        try:
            raw_articles = await feed.fetch()
            all_raw.extend(raw_articles)
        except Exception as e:
            logger.error(f"Feed {feed.source_id} crashed: {e}")

    logger.info(f"Collected {len(all_raw)} raw articles across all feeds")

    # --- Step 2: deduplicate and insert ---
    inserted = 0
    skipped = 0
    batch_accepted_titles: list[str] = []  # titles accepted so far this cycle

    for raw in all_raw:
        if not raw.title or not raw.url:
            continue

        fp = make_fingerprint(raw.title)

        # Within-batch dedup first (catches cross-feed duplicates before Redis state is updated)
        if _within_batch_duplicate(raw.title, batch_accepted_titles):
            skipped += 1
            await upsert_dedup_log(pool, fp, None)
            continue

        # Then check against Redis (previous cycles)
        duplicate = await is_duplicate(raw.title, redis)
        if duplicate:
            skipped += 1
            await upsert_dedup_log(pool, fp, None)
            continue

        article = normalize(raw)
        article_id = await upsert_article(pool, article)
        if article_id:
            await upsert_dedup_log(pool, fp, article_id)
            batch_accepted_titles.append(raw.title)
            inserted += 1
        else:
            # guid already existed in DB
            skipped += 1

    logger.info(f"Fetch cycle done: {inserted} inserted, {skipped} skipped/duplicate")

    # --- Step 3: trim, score, notify ---
    await trim_old_articles(pool, keep=200, per_source=15)

    since = datetime.now(timezone.utc) - timedelta(hours=1)
    new_count = await get_new_article_count_since(pool, since)
    recent = await get_recent_articles(pool, limit=20)
    factors = compute_global_score(recent, new_count)
    await insert_defcon_history(pool, factors, len(recent))
    logger.info(f"Defcon score: {factors.total:.1f} (level {factors.level} - {factors.label})")

    await pool.execute("UPDATE last_refresh SET refreshed_at = NOW() WHERE id = 1")
    await publish_cache_invalidation()


def reschedule():
    interval = settings.fetch_interval_minutes
    scheduler.reschedule_job("fetch_cycle", trigger="interval", minutes=interval)


def start_scheduler():
    interval = settings.fetch_interval_minutes
    scheduler.add_job(
        run_fetch_cycle,
        trigger="interval",
        minutes=interval,
        id="fetch_cycle",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.start()
    logger.info(f"Scheduler started — fetch every {interval} minutes")
