"""Normalize raw feed articles into a canonical shape."""
from feeds.base import RawArticle
from pipeline.summary import make_summary
from pipeline.scorer import compute_article_score


def normalize(raw: RawArticle) -> dict:
    summary = make_summary(raw.summary or raw.raw_text or "")
    defcon_score = compute_article_score(raw.title, summary)

    return {
        "guid": raw.guid,
        "title": raw.title,
        "summary": summary,
        "url": raw.url,
        "source": raw.source,
        "published_at": raw.published_at,
        "raw_categories": raw.categories,
        "defcon_score": defcon_score,
    }
