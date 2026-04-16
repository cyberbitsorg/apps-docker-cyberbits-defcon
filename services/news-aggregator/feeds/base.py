from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


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
    feed_url: str

    @abstractmethod
    async def fetch(self) -> list[RawArticle]:
        """Fetch and parse articles from this source."""
        ...
