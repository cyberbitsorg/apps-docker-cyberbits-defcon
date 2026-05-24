"""
One-shot backfill script: recomputes defcon_score and defcon_trigger for all
non-deleted articles using the v2 scorer.

Run from within services/news-aggregator/:
    python -m scripts.backfill_article_scores
    python scripts/backfill_article_scores.py
"""
import asyncio
import sys
import os

# Ensure the service root is on sys.path so pipeline.* and config are importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncpg

from config import settings
from pipeline.scoring import compute_article_score

FETCH_QUERY = "SELECT id, title, summary FROM articles WHERE is_deleted = FALSE"
UPDATE_QUERY = "UPDATE articles SET defcon_score=$1, defcon_trigger=$2 WHERE id=$3"
PROGRESS_EVERY = 50


async def main() -> None:
    pool = await asyncpg.create_pool(settings.database_url, min_size=1, max_size=5)
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(FETCH_QUERY)

        total = len(rows)
        print(f"Backfill starting: {total} articles to process")

        updated = 0
        errors = 0

        async with pool.acquire() as conn:
            for idx, row in enumerate(rows, start=1):
                article_id = row["id"]
                title = row["title"] or ""
                summary = row["summary"] or ""

                try:
                    result = compute_article_score(title, summary)
                    await conn.execute(UPDATE_QUERY, result.score, result.trigger, article_id)
                    updated += 1
                except Exception as exc:
                    errors += 1
                    print(f"  ERROR article {article_id}: {exc}")

                if idx % PROGRESS_EVERY == 0:
                    print(f"  Progress: {idx}/{total} processed ({errors} errors so far)")

        print(f"Backfill complete: {updated} updated, {errors} errors, {total} total")
    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(main())
