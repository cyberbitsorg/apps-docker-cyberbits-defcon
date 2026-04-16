import logging
import re
from datetime import timezone

import feedparser
import httpx
from dateutil import parser as dateparser

from feeds.base import BaseFeedParser, RawArticle

logger = logging.getLogger(__name__)


class CyberScoopFeed(BaseFeedParser):
    source_id = "cyberscoop"
    feed_url = "https://cyberscoop.com/feed/"

    async def fetch(self) -> list[RawArticle]:
        try:
            async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                response = await client.get(
                    self.feed_url,
                    headers={"User-Agent": "Mozilla/5.0 (compatible; DefconBot/1.0)"},
                )
                response.raise_for_status()
                content = response.text
        except Exception as e:
            logger.error(f"[CS] Failed to fetch feed: {e}")
            return []

        feed = feedparser.parse(content)
        articles = []

        for entry in feed.entries:
            try:
                published = _parse_date(entry.get("published", ""))
                if published is None:
                    continue

                summary = _strip_html(entry.get("summary", "") or entry.get("description", ""))
                categories = [tag.term for tag in entry.get("tags", [])] if entry.get("tags") else []

                articles.append(RawArticle(
                    guid=entry.get("id") or entry.get("link", ""),
                    title=entry.get("title", "").strip(),
                    url=entry.get("link", ""),
                    summary=summary,
                    source=self.source_id,
                    published_at=published,
                    categories=categories,
                    raw_text=summary,
                ))
            except Exception as e:
                logger.warning(f"[CS] Skipping entry: {e}")

        logger.info(f"[CS] Fetched {len(articles)} articles")
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
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
