import asyncio
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

import feedparser
import httpx
from dateutil import parser as dateparser

logger = logging.getLogger(__name__)

_BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


@dataclass
class RawArticle:
    guid: str
    title: str
    url: str
    summary: str
    source: str
    published_at: datetime
    categories: list[str] = field(default_factory=list)
    raw_text: str = ""


class BaseFeedParser(ABC):
    source_id: str

    @abstractmethod
    async def fetch(self) -> list[RawArticle]:
        """Fetch and parse articles from this source."""
        ...


class RssFeedParser(BaseFeedParser):
    feed_url: str

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if "feed_url" not in cls.__dict__:
            raise TypeError(f"{cls.__name__} must define class attribute feed_url")
        if "source_id" not in cls.__dict__:
            raise TypeError(f"{cls.__name__} must define class attribute source_id")

    async def fetch(self) -> list[RawArticle]:
        delays = [5, 15, 45]
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            for attempt, delay in enumerate(delays + [None], start=1):
                try:
                    response = await client.get(
                        self.feed_url,
                        headers={"User-Agent": _BROWSER_UA},
                    )
                    if response.status_code == 429:
                        if delay is None:
                            logger.error(f"[{self.source_id}] Still 429 after {len(delays)} retries, giving up")
                            return []
                        retry_after = int(response.headers.get("Retry-After", delay))
                        logger.warning(f"[{self.source_id}] 429 on attempt {attempt}, retrying in {retry_after}s")
                        await asyncio.sleep(retry_after)
                        continue
                    response.raise_for_status()
                    content = response.text
                    break
                except Exception as e:
                    logger.error(f"[{self.source_id}] Failed to fetch feed: {e}")
                    return []

        feed = feedparser.parse(content)
        articles = []

        for entry in feed.entries:
            try:
                article = self._build_article(entry)
                if article:
                    articles.append(article)
            except Exception as e:
                logger.warning(f"[{self.source_id}] Skipping entry: {e}")

        logger.info(f"[{self.source_id}] Fetched {len(articles)} articles")
        return articles

    def _build_article(self, entry) -> Optional[RawArticle]:
        date_str = entry.get("published", "") or entry.get("updated", "")
        published = _parse_date(date_str)
        if published is None:
            return None

        summary = _strip_html(entry.get("summary", "") or entry.get("description", ""))
        categories = [tag.term for tag in entry.get("tags", [])] if entry.get("tags") else []

        return RawArticle(
            guid=entry.get("id") or entry.get("link") or "",
            title=entry.get("title", "").strip(),
            url=entry.get("link", ""),
            summary=summary,
            source=self.source_id,
            published_at=published,
            categories=categories,
            raw_text=summary,
        )


def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None
    try:
        dt = dateparser.parse(date_str)
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            # Normalise to stdlib timezone.utc so callers can use `== timezone.utc`
            dt = dt.astimezone(timezone.utc)
        return dt
    except Exception:
        return None


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
