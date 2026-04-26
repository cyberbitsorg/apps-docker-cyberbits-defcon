import pytest
import respx
import httpx
from feeds.security_affairs import SecurityAffairsFeed

SAMPLE_POSTS = [
    {
        "id": 12345,
        "link": "https://securityaffairs.com/12345/malware/test-article.html",
        "title": {"rendered": "Test &amp; Security Article"},
        "excerpt": {"rendered": "<p>A summary about <b>malware</b>.</p>"},
        "date_gmt": "2026-04-24T10:00:00",
        "categories": [3, 7],
    },
    {
        "id": 12346,
        "link": "https://securityaffairs.com/12346/apt/another.html",
        "title": {"rendered": "Another Article"},
        "excerpt": {"rendered": "<p>Another summary.</p>"},
        "date_gmt": "2026-04-23T08:30:00",
        "categories": [1],
    },
]


@pytest.mark.asyncio
async def test_security_affairs_returns_articles():
    feed = SecurityAffairsFeed()
    with respx.mock:
        respx.get(
            "https://securityaffairs.com/wp-json/wp/v2/posts",
            params={"per_page": "100"},
        ).mock(return_value=httpx.Response(200, json=SAMPLE_POSTS))
        articles = await feed.fetch()

    assert len(articles) == 2
    a = articles[0]
    assert a.source == "security_affairs"
    assert a.guid == "12345"
    assert a.title == "Test & Security Article"
    assert a.url == "https://securityaffairs.com/12345/malware/test-article.html"
    assert a.published_at.year == 2026
    assert a.categories == ["3", "7"]


@pytest.mark.asyncio
async def test_security_affairs_returns_empty_on_error():
    feed = SecurityAffairsFeed()
    with respx.mock:
        respx.get(
            "https://securityaffairs.com/wp-json/wp/v2/posts",
            params={"per_page": "100"},
        ).mock(return_value=httpx.Response(500))
        articles = await feed.fetch()

    assert articles == []
