import logging
from datetime import datetime, timezone

import asyncpg

logger = logging.getLogger(__name__)


async def upsert_article(pool: asyncpg.Pool, article: dict) -> str | None:
    """Insert article, ignoring duplicates (by guid). Returns the article id or None."""
    published_at = article["published_at"]
    if published_at and published_at > datetime.now(timezone.utc):
        published_at = datetime.now(timezone.utc)
    try:
        row = await pool.fetchrow(
            """
            INSERT INTO articles (guid, title, summary, url, source, published_at, raw_categories, defcon_score)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (guid) DO NOTHING
            RETURNING id
            """,
            article["guid"],
            article["title"],
            article["summary"],
            article["url"],
            article["source"],
            published_at,
            article["raw_categories"],
            article["defcon_score"],
        )
        return str(row["id"]) if row else None
    except Exception as e:
        logger.error(f"upsert_article error: {e}")
        return None


async def upsert_dedup_log(pool: asyncpg.Pool, fingerprint: str, canonical_id: str | None):
    try:
        await pool.execute(
            """
            INSERT INTO dedup_log (fingerprint, canonical_id, duplicate_count)
            VALUES ($1, $2::uuid, 0)
            ON CONFLICT (fingerprint) DO UPDATE
              SET duplicate_count = dedup_log.duplicate_count + 1,
                  last_seen_at = NOW()
            """,
            fingerprint,
            canonical_id,
        )
    except Exception as e:
        logger.warning(f"upsert_dedup_log error: {e}")


async def trim_old_articles(pool: asyncpg.Pool, keep: int = 200, per_source: int = 15):
    """
    Soft-delete old articles while guaranteeing each source keeps at least
    `per_source` recent articles. Then fill remaining slots by recency.
    """
    await pool.execute(
        """
        WITH per_source_keep AS (
            -- Top `per_source` articles per source
            SELECT id FROM (
                SELECT id,
                       ROW_NUMBER() OVER (PARTITION BY source ORDER BY published_at DESC) AS rn
                FROM articles
                WHERE is_deleted = FALSE
            ) ranked
            WHERE rn <= $2
        ),
        recency_keep AS (
            -- Top `keep` overall by recency
            SELECT id FROM articles
            WHERE is_deleted = FALSE
            ORDER BY published_at DESC
            LIMIT $1
        ),
        keep_ids AS (
            SELECT id FROM per_source_keep
            UNION
            SELECT id FROM recency_keep
        )
        UPDATE articles
        SET is_deleted = TRUE
        WHERE id NOT IN (SELECT id FROM keep_ids)
        AND is_deleted = FALSE
        """,
        keep,
        per_source,
    )


async def get_recent_articles(pool: asyncpg.Pool, limit: int = 20) -> list[dict]:
    rows = await pool.fetch(
        """
        SELECT id, title, summary, source, defcon_score
        FROM articles
        WHERE is_deleted = FALSE
        ORDER BY published_at DESC
        LIMIT $1
        """,
        limit,
    )
    return [dict(r) for r in rows]


async def get_new_article_count_since(pool: asyncpg.Pool, since: datetime) -> int:
    row = await pool.fetchrow(
        "SELECT COUNT(*) FROM articles WHERE fetched_at >= $1 AND is_deleted = FALSE",
        since,
    )
    return int(row["count"])
