"""Normalize raw feed articles into a canonical shape."""
from feeds.base import RawArticle
from pipeline.summary import make_summary
from pipeline.scorer import compute_article_score
from pipeline.scoring_v2 import compute_article_score_v2
from config import settings


def normalize(raw: RawArticle) -> dict:
    summary = make_summary(raw.summary or raw.raw_text or "")

    if settings.scorer_version == "v2":
        result = compute_article_score_v2(raw.title, summary)
        defcon_score = result.score
        defcon_trigger = result.trigger
    else:
        defcon_score = compute_article_score(raw.title, summary)
        defcon_trigger = None

    return {
        "guid": raw.guid,
        "title": raw.title,
        "summary": summary,
        "url": raw.url,
        "source": raw.source,
        "published_at": raw.published_at,
        "raw_categories": raw.categories,
        "defcon_score": defcon_score,
        "defcon_trigger": defcon_trigger,
    }
