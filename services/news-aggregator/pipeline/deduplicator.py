"""
Two-layer deduplication:
  Layer 1 — Fast:   SHA-256 of normalized title tokens (Redis SET, O(1))
  Layer 2 — Slow:   TF-IDF cosine similarity OR Jaccard token overlap,
                    whichever fires first, vs last 50 titles
"""
import hashlib
import logging
import re

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

STOP_WORDS = frozenset({
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "has", "have", "had", "it", "its", "as", "this", "that", "these", "those",
    "how", "what", "when", "where", "who", "why", "will", "can", "could",
    "would", "should", "may", "might", "do", "does", "did", "not", "no",
    "up", "out", "so", "than", "into", "over", "after", "new", "using",
    "via", "says", "say", "said", "report", "reports", "found", "finds",
    "warns", "warn", "reveals", "reveal", "shows", "show",
})

# TF-IDF: catch paraphrased headlines with high vocabulary overlap
TFIDF_THRESHOLD = 0.55

# Jaccard: catch headlines sharing key proper nouns even when phrased very differently.
# "Apple iOS DarkSword update" vs "Apple patches DarkSword iOS devices" → high token overlap.
JACCARD_THRESHOLD = 0.35

# Minimum meaningful token length — skip noise like "18" or "2"
MIN_TOKEN_LEN = 3

# Month names — used for temporal conflict detection (e.g. "February Patch Tuesday" ≠ "March Patch Tuesday")
_MONTHS = frozenset({
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
    "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "oct", "nov", "dec",
})
_YEAR_RE = re.compile(r"\b(20\d{2})\b")

RECENT_TITLES_KEY = "dedup:recent_titles"
FINGERPRINTS_KEY = "dedup:fingerprints"
RECENT_TITLES_MAX = 300
FINGERPRINT_TTL = 7 * 24 * 3600  # 7 days


def _token_set(title: str) -> frozenset[str]:
    """Lowercase, strip punctuation, drop stop words and short tokens."""
    title = title.lower()
    title = re.sub(r"[^\w\s]", " ", title)
    return frozenset(
        t for t in title.split()
        if t and t not in STOP_WORDS and len(t) >= MIN_TOKEN_LEN
    )


def normalize_title(title: str) -> str:
    """Sorted token string used for SHA-256 fingerprinting (Layer 1)."""
    tokens = sorted(_token_set(title))
    return " ".join(tokens)


def fingerprint(title: str) -> str:
    return hashlib.sha256(normalize_title(title).encode()).hexdigest()


def _jaccard(a: frozenset, b: frozenset) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _temporal_conflict(title_a: str, title_b: str) -> bool:
    """Return True if titles reference different months or different years — meaning they can't be the same story."""
    a, b = title_a.lower(), title_b.lower()

    months_a = {w for w in a.split() if w in _MONTHS}
    months_b = {w for w in b.split() if w in _MONTHS}
    if months_a and months_b and months_a != months_b:
        return True

    years_a = set(_YEAR_RE.findall(a))
    years_b = set(_YEAR_RE.findall(b))
    if years_a and years_b and years_a != years_b:
        return True

    return False


async def is_duplicate(title: str, redis_client) -> bool:
    """
    Returns True if the article is a duplicate (should be skipped).
    Mutates Redis state when NOT a duplicate.
    """
    fp = fingerprint(title)

    # --- Layer 1: exact/near-exact fingerprint ---
    exists = await redis_client.sismember(FINGERPRINTS_KEY, fp)
    if exists:
        logger.debug(f"[Dedup L1] Fingerprint match: {title[:70]}")
        return True

    # --- Layer 2: semantic similarity vs recent 50 titles ---
    recent_raw = await redis_client.lrange(RECENT_TITLES_KEY, 0, RECENT_TITLES_MAX - 1)
    recent_titles = [t.decode() if isinstance(t, bytes) else t for t in recent_raw]

    if recent_titles:
        new_tokens = _token_set(title)

        # 2a — Jaccard overlap (fast, catches proper-noun matches)
        for existing in recent_titles:
            if _temporal_conflict(title, existing):
                continue
            j = _jaccard(new_tokens, _token_set(existing))
            if j >= JACCARD_THRESHOLD:
                logger.info(f"[Dedup L2-J] Jaccard={j:.2f} duplicate: '{title[:60]}' ≈ '{existing[:60]}'")
                return True

        # 2b — TF-IDF cosine similarity (catches paraphrases)
        # Filter out temporal conflicts before building the comparison corpus
        comparable_titles = [t for t in recent_titles if not _temporal_conflict(title, t)]
        if comparable_titles:
            try:
                corpus = comparable_titles + [title]
                vectorizer = TfidfVectorizer(min_df=1, stop_words="english", ngram_range=(1, 2))
                tfidf_matrix = vectorizer.fit_transform(corpus)
                new_vec = tfidf_matrix[-1]
                existing_vecs = tfidf_matrix[:-1]
                sims = cosine_similarity(new_vec, existing_vecs).flatten()
                max_sim = float(np.max(sims))
                if max_sim >= TFIDF_THRESHOLD:
                    best_match = comparable_titles[int(np.argmax(sims))]
                    logger.info(f"[Dedup L2-T] TF-IDF={max_sim:.2f} duplicate: '{title[:60]}' ≈ '{best_match[:60]}'")
                    return True
            except Exception as e:
                logger.warning(f"[Dedup L2-T] TF-IDF error: {e}")

    # Not a duplicate — register
    await redis_client.sadd(FINGERPRINTS_KEY, fp)
    await redis_client.expire(FINGERPRINTS_KEY, FINGERPRINT_TTL)
    await redis_client.lpush(RECENT_TITLES_KEY, title)
    await redis_client.ltrim(RECENT_TITLES_KEY, 0, RECENT_TITLES_MAX - 1)

    return False
