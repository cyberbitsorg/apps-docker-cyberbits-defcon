import logging
import json

import asyncpg

from pipeline.scorer import DefconFactors
from pipeline.scoring_v2 import GlobalScore

logger = logging.getLogger(__name__)


async def insert_defcon_history_v1(pool: asyncpg.Pool, factors: DefconFactors, article_window: int):
    try:
        await pool.execute(
            """
            INSERT INTO defcon_history (score, level, article_window, contributing_factors)
            VALUES ($1, $2, $3, $4::jsonb)
            """,
            factors.total,
            factors.level,
            article_window,
            json.dumps(factors.to_dict()),
        )
    except Exception as e:
        logger.error(f"insert_defcon_history_v1 error: {e}")


async def insert_defcon_history_v2(
    pool: asyncpg.Pool,
    g: GlobalScore,
    raw_level: int,
    displayed_level: int,
    article_window: int,
):
    factors = {
        "trigger": g.trigger,
        "weighted_max": g.weighted_max,
        "volume_bonus": g.volume_bonus,
        "raw_level": raw_level,
        "displayed_level": displayed_level,
    }
    if g.trigger_article_id is not None:
        factors["trigger_article_id"] = g.trigger_article_id
        factors["trigger_article_title"] = g.trigger_article_title
        if g.trigger_article_published_at is not None:
            factors["trigger_article_published_at"] = g.trigger_article_published_at.isoformat()
    try:
        await pool.execute(
            """
            INSERT INTO defcon_history (score, level, article_window, contributing_factors)
            VALUES ($1, $2, $3, $4::jsonb)
            """,
            g.score,
            displayed_level,
            article_window,
            json.dumps(factors),
        )
    except Exception as e:
        logger.error(f"insert_defcon_history_v2 error: {e}")


# Backwards-compatible alias for any callers still importing the old name
insert_defcon_history = insert_defcon_history_v1
