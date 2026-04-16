import logging
from datetime import timezone

import feedparser
import httpx
from dateutil import parser as dateparser

from feeds.base import BaseFeedParser, RawArticle

logger = logging.getLogger(__name__)


class TheHackerNewsFeed(BaseFeedParser):
    source_id = "the_hacker_news"
    feed_url = "https://feeds.feedburner.com/TheHackersNews"

    async def fetch(self) -> list[RawArticle]:
        try:
            async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                response = await client.get(self.feed_url)
                response.raise_for_status()
                content = response.text
        except Exception as e:
            logger.error(f"[THN] Failed to fetch feed: {e}")
            return []

        feed = feedparser.parse(content)
        articles = []

        for entry in feed.entries:
            try:
                published = _parse_date(entry.get("published", ""))
                if published is None:
                    continue

                summary = entry.get("summary", "") or entry.get("description", "")
                summary = _strip_html(summary)

                articles.append(RawArticle(
                    guid=entry.get("id") or entry.get("link", ""),
                    title=entry.get("title", "").strip(),
                    url=entry.get("link", ""),
                    summary=summary,
                    source=self.source_id,
                    published_at=published,
                    categories=[],
                    raw_text=summary,
                ))
            except Exception as e:
                logger.warning(f"[THN] Skipping entry: {e}")

        logger.info(f"[THN] Fetched {len(articles)} articles")
        return articles


def _parse_date(date_str: str):
    if not date_str:
        return None
    try:
        dt = dateparser.parse(date_str)
        if dt and dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _strip_html(text: str) -> str:
    import re
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
