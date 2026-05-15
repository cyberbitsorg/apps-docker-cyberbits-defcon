"""
One-shot cleanup: applies current dedup logic retroactively to articles
already in the DB. Newer articles are kept; older duplicates are soft-deleted
(is_deleted = TRUE).

Dry-run by default. Pass --apply to actually delete.

Run from within services/news-aggregator/:
    python -m scripts.dedup_existing_articles            # dry run
    python -m scripts.dedup_existing_articles --apply    # commit deletes
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncpg

from config import settings
from pipeline.deduplicator import (
    _token_set, _jaccard, _temporal_conflict,
    _shared_named_phrase, _shared_actor_and_token,
    _shared_vendor_product, _extract_cves,
    JACCARD_THRESHOLD,
)

FETCH_QUERY = """
    SELECT id, title, COALESCE(summary, '') AS summary, published_at
    FROM articles
    WHERE is_deleted = FALSE
    ORDER BY published_at DESC
"""

DELETE_QUERY = "UPDATE articles SET is_deleted = TRUE WHERE id = $1"


def _duplicate_reason(
    title: str,
    summary: str,
    kept: list[dict],
) -> tuple[str, dict] | None:
    """Return (reason, kept_article) if `title`/`summary` duplicates any kept article."""
    new_tokens = _token_set(title)
    new_cves = _extract_cves(f"{title} {summary}")
    for k in kept:
        k_title = k["title"]
        if _temporal_conflict(title, k_title):
            continue
        if new_cves:
            shared = new_cves & _extract_cves(f"{k_title} {k['summary']}")
            if shared:
                return (f"CVE {next(iter(shared))}", k)
        if _shared_named_phrase(title, k_title):
            return ("shared named phrase", k)
        if _shared_actor_and_token(title, k_title):
            return ("shared threat actor", k)
        pair = _shared_vendor_product(title, k_title)
        if pair:
            pair_tokens = frozenset(pair.split())
            if (new_tokens - pair_tokens) & (_token_set(k_title) - pair_tokens):
                return (f"vendor+product '{pair}'", k)
        j = _jaccard(new_tokens, _token_set(k_title))
        if j >= JACCARD_THRESHOLD:
            return (f"Jaccard={j:.2f}", k)
    return None


async def main() -> None:
    apply = "--apply" in sys.argv

    pool = await asyncpg.create_pool(settings.database_url, min_size=1, max_size=5)
    try:
        rows = await pool.fetch(FETCH_QUERY)
        # Walk newest → oldest. First-seen wins (newest article kept), older dupes deleted.
        print(f"Scanning {len(rows)} active articles (newest → oldest)")

        kept: list[dict] = []
        to_delete: list[dict] = []

        for r in rows:
            article = {
                "id": r["id"], "title": r["title"], "summary": r["summary"],
                "published_at": r["published_at"],
            }
            dup = _duplicate_reason(article["title"], article["summary"], kept)
            if dup is not None:
                reason, winner = dup
                to_delete.append({**article, "reason": reason, "winner": winner["title"]})
            else:
                kept.append(article)

        print(f"\nWould delete {len(to_delete)} duplicates, keep {len(kept)}\n")
        for d in to_delete:
            print(f"  [{d['reason']:30s}] '{d['title'][:70]}'")
            print(f"  {'':30s}    ⤷ kept: '{d['winner'][:70]}'")

        if not apply:
            print("\nDry run only. Re-run with --apply to commit deletes.")
            return

        async with pool.acquire() as conn:
            async with conn.transaction():
                for d in to_delete:
                    await conn.execute(DELETE_QUERY, d["id"])
        print(f"\nDeleted {len(to_delete)} articles.")
    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(main())
