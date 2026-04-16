import logging

import asyncpg

from pipeline.scorer import DefconFactors

logger = logging.getLogger(__name__)


async def insert_defcon_history(pool: asyncpg.Pool, factors: DefconFactors, article_window: int):
    try:
        import json
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
        logger.error(f"insert_defcon_history error: {e}")
