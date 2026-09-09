import pytest
import respx
import httpx
from feeds.hackread import HackReadFeed

SAMPLE_POSTS = [
    {
        "id": 149646,
        "link": "https://hackread.com/real-time-vendor-risk-monitoring-platforms/",
        "title": {"rendered": "Top 5 Real-Time Vendor Risk Monitoring Platforms 2026"},
        "excerpt": {"rendered": "<p>Compare the 5 best <b>monitoring platforms</b> of 2026.</p>\n"},
        "date_gmt": "2026-09-08T17:40:04",
        "categories": [9],
    },
    {
        "id": 149640,
        "link": "https://hackread.com/example-ransomware-post/",
        "title": {"rendered": "Ransomware Gang Hits Example Corp"},
        "excerpt": {"rendered": "<p>A breach summary.</p>"},
        "date_gmt": "2026-09-07T12:00:00",
        "categories": [3, 7],
    },
]


@pytest.mark.asyncio
async def test_hackread_returns_articles():
    feed = HackReadFeed()
    with respx.mock:
        respx.get(
            "https://hackread.com/wp-json/wp/v2/posts",
            params={"per_page": "100"},
        ).mock(return_value=httpx.Response(200, json=SAMPLE_POSTS))
        articles = await feed.fetch()

    assert len(articles) == 2
    a = articles[0]
    assert a.source == "hackread"
    assert a.guid == "149646"
    assert a.title == "Top 5 Real-Time Vendor Risk Monitoring Platforms 2026"
    assert a.url == "https://hackread.com/real-time-vendor-risk-monitoring-platforms/"
    assert a.published_at.year == 2026 and a.published_at.month == 9
    assert a.categories == ["9"]


@pytest.mark.asyncio
async def test_hackread_skips_posts_without_date():
    posts = [dict(SAMPLE_POSTS[0], date_gmt="")]
    feed = HackReadFeed()
    with respx.mock:
        respx.get(
            "https://hackread.com/wp-json/wp/v2/posts",
            params={"per_page": "100"},
        ).mock(return_value=httpx.Response(200, json=posts))
        articles = await feed.fetch()

    assert articles == []


@pytest.mark.asyncio
async def test_hackread_returns_empty_on_cloudflare_challenge():
    feed = HackReadFeed()
    with respx.mock:
        respx.get(
            "https://hackread.com/wp-json/wp/v2/posts",
            params={"per_page": "100"},
        ).mock(return_value=httpx.Response(403, headers={"cf-mitigated": "challenge"}))
        articles = await feed.fetch()

    assert articles == []


@pytest.mark.asyncio
async def test_hackread_returns_empty_on_error():
    feed = HackReadFeed()
    with respx.mock:
        respx.get(
            "https://hackread.com/wp-json/wp/v2/posts",
            params={"per_page": "100"},
        ).mock(return_value=httpx.Response(500))
        articles = await feed.fetch()

    assert articles == []
