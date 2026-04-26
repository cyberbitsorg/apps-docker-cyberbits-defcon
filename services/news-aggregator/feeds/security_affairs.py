import html
import logging

import httpx

from feeds.base import BaseFeedParser, RawArticle, _BROWSER_UA, _parse_date, _strip_html

logger = logging.getLogger(__name__)

_API_URL = "https://securityaffairs.com/wp-json/wp/v2/posts"


class SecurityAffairsFeed(BaseFeedParser):
    source_id = "security_affairs"

    async def fetch(self) -> list[RawArticle]:
        try:
            async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                response = await client.get(
                    _API_URL,
                    params={"per_page": "100"},
                    headers={"User-Agent": _BROWSER_UA},
                )
                response.raise_for_status()
                posts = response.json()
        except Exception as e:
            logger.error(f"[security_affairs] Failed to fetch: {e}")
            return []

        articles = []
        for post in posts:
            try:
                published = _parse_date(post.get("date_gmt", ""))
                if published is None:
                    continue

                title = html.unescape(_strip_html(post["title"]["rendered"])).strip()
                summary = html.unescape(_strip_html(post["excerpt"]["rendered"]))
                categories = [str(c) for c in post.get("categories", [])]

                articles.append(RawArticle(
                    guid=str(post["id"]),
                    title=title,
                    url=post["link"],
                    summary=summary,
                    source=self.source_id,
                    published_at=published,
                    categories=categories,
                    raw_text=summary,
                ))
            except Exception as e:
                logger.warning(f"[security_affairs] Skipping post {post.get('id')}: {e}")

        logger.info(f"[security_affairs] Fetched {len(articles)} articles")
        return articles
