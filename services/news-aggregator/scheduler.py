import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import settings
from db.connection import get_pool
from db.articles import upsert_article, upsert_dedup_log, trim_old_articles, get_new_article_count_since, get_articles_in_window
from db.defcon import insert_defcon_history
from db.sticky_level import read_sticky_state, write_sticky_state, compute_displayed_level
from pipeline.scoring import compute_global_score, _current_window_hours
from cache.redis_client import get_redis, publish_cache_invalidation
from cache.volume import record_volume, get_volume_baseline
from pipeline.deduplicator import is_duplicate, fingerprint as make_fingerprint, is_batch_duplicate, RECENT_TITLES_KEY
from pipeline.triggers import detect_trigger
from pipeline.normalizer import normalize
from feeds.bleeping_computer import BleepingComputerFeed
from feeds.hacker_news import HackerNewsFeed
from feeds.hackread import HackReadFeed
from feeds.security_affairs import SecurityAffairsFeed
from feeds.the_register import TheRegisterFeed

logger = logging.getLogger(__name__)


def _level_from_score(score: float) -> int:
    if score >= 80:
        return 1
    if score >= 60:
        return 2
    if score >= 40:
        return 3
    if score >= 20:
        return 4
    return 5


FEEDS = [
    BleepingComputerFeed(),
    HackerNewsFeed(),
    HackReadFeed(),
    SecurityAffairsFeed(),
    TheRegisterFeed(),
]

scheduler = AsyncIOScheduler()


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
    batch_accepted: list[tuple[str, str, Optional[str]]] = []  # (title, summary, trigger_name) accepted so far

    for raw in all_raw:
        if not raw.title or not raw.url:
            continue

        fp = make_fingerprint(raw.title)

        # Within-batch dedup first (catches cross-feed duplicates before Redis state is updated)
        if is_batch_duplicate(raw.title, raw.summary or "", batch_accepted):
            skipped += 1
            await upsert_dedup_log(pool, fp, None)
            continue

        # Then check against Redis (previous cycles)
        duplicate = await is_duplicate(raw.title, redis, summary=raw.summary or "")
        if duplicate:
            skipped += 1
            await upsert_dedup_log(pool, fp, None)
            continue

        article = normalize(raw)
        article_id = await upsert_article(pool, article)
        if article_id:
            await upsert_dedup_log(pool, fp, article_id)
            _t = detect_trigger(f"{raw.title} {raw.summary or ''}")
            batch_accepted.append((raw.title, raw.summary or "", _t.trigger if _t else None))
            inserted += 1
        else:
            # guid already existed in DB
            skipped += 1

    logger.info(f"Fetch cycle done: {inserted} inserted, {skipped} skipped/duplicate")

    # --- Step 3: trim, score, notify ---
    trimmed_titles = await trim_old_articles(pool, keep=100, per_source=15)
    if trimmed_titles:
        pipe = redis.pipeline(transaction=False)
        for title in trimmed_titles:
            pipe.lrem(RECENT_TITLES_KEY, 1, title)
        await pipe.execute()

    since = datetime.now(timezone.utc) - timedelta(hours=1)
    new_count = await get_new_article_count_since(pool, since)
    await record_volume(redis, new_count)
    avg_vol = await get_volume_baseline(redis)

    now_utc = datetime.now(timezone.utc)
    active_window_hours = _current_window_hours(now_utc)
    window = await get_articles_in_window(pool, hours=72)
    g = compute_global_score(
        window,
        new_count=new_count,
        baseline=avg_vol,
        window_hours=active_window_hours,
    )
    raw_level = _level_from_score(g.score)
    sticky_state = await read_sticky_state(pool)
    sticky_result = compute_displayed_level(raw_level, sticky_state, now_utc)
    await write_sticky_state(pool, sticky_result)
    await insert_defcon_history(
        pool, g,
        raw_level=raw_level,
        displayed_level=sticky_result.displayed_level,
        article_window=len(window),
    )
    logger.info(
        f"Defcon score: {g.score:.1f} (raw level {raw_level}, displayed {sticky_result.displayed_level}, trigger={g.trigger})"
    )

    await pool.execute(
        """
        INSERT INTO last_refresh (id, refreshed_at) VALUES (1, NOW())
        ON CONFLICT (id) DO UPDATE SET refreshed_at = NOW()
        """
    )
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
