"""
Two-layer deduplication:
  Layer 1 — Fast:   SHA-256 of normalized title tokens (Redis SET, O(1))
  Layer 2 — Slow:   TF-IDF cosine similarity OR Jaccard token overlap,
                    whichever fires first, vs last 50 titles
"""
import hashlib
import logging
import re
from typing import Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from pipeline.vocabulary import THREAT_ACTORS

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
TFIDF_THRESHOLD = 0.45

# Jaccard: catch headlines sharing key proper nouns even when phrased very differently.
# "Apple iOS DarkSword update" vs "Apple patches DarkSword iOS devices" → high token overlap.
JACCARD_THRESHOLD = 0.28

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
CVES_KEY = "dedup:cves"
RECENT_TITLES_MAX = 300
FINGERPRINT_TTL = 7 * 24 * 3600  # 7 days
CVE_TTL = 36 * 3600  # 36h — long enough to span overnight news churn, short enough to allow later stories

# CVE-2024-1234, CVE-2024-12345, CVE 2024 12345 (incl. en/em dashes & spaces)
_CVE_ID_RE = re.compile(r"\bCVE[-–— ]?(\d{4})[-–— ]?(\d{3,7})\b", re.IGNORECASE)

# Known vendor → product proper-noun pairs. When two articles share a pair AND any
# other meaningful token, treat as duplicate. Tokens are matched lowercase, with
# word boundaries — product names may contain spaces or hyphens.
VENDOR_PRODUCT_PAIRS: tuple[tuple[str, str], ...] = (
    ("cisco", "sd-wan"), ("cisco", "ios"), ("cisco", "catalyst"), ("cisco", "asa"),
    ("microsoft", "exchange"), ("microsoft", "sharepoint"), ("microsoft", "windows"),
    ("microsoft", "azure"), ("microsoft", "outlook"), ("microsoft", "teams"),
    ("apple", "ios"), ("apple", "macos"), ("apple", "safari"),
    ("google", "chrome"), ("google", "android"),
    ("fortinet", "fortigate"), ("fortinet", "fortios"), ("fortinet", "fortimanager"),
    ("ivanti", "epmm"), ("ivanti", "connect secure"), ("ivanti", "endpoint manager"),
    ("palo alto", "pan-os"), ("vmware", "esxi"), ("vmware", "vcenter"),
    ("citrix", "netscaler"), ("citrix", "adc"),
    ("sonicwall", "sma"), ("sonicwall", "firewall"),
    ("oracle", "weblogic"), ("oracle", "java"),
    ("openssh", ""), ("openssl", ""), ("nginx", ""), ("apache", "struts"),
    ("wordpress", ""), ("drupal", ""), ("git", ""), ("curl", ""),
)


def _extract_cves(text: str) -> frozenset[str]:
    """Return canonical CVE IDs (e.g. 'CVE-2024-1234') found in text."""
    out = set()
    for m in _CVE_ID_RE.finditer(text or ""):
        out.add(f"CVE-{m.group(1)}-{m.group(2)}")
    return frozenset(out)


def _shared_vendor_product(text_a: str, text_b: str) -> Optional[str]:
    """Return the shared vendor-product pair label if both texts mention it, else None."""
    a, b = text_a.lower(), text_b.lower()
    for vendor, product in VENDOR_PRODUCT_PAIRS:
        if vendor not in a or vendor not in b:
            continue
        if product and (product not in a or product not in b):
            continue
        return f"{vendor} {product}".strip()
    return None


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


# Matches quoted phrases (straight and curly quotes)
_QUOTED_RE = re.compile(r"['\"‘’“”]([^'\"]{4,})['\"‘’“”]")


def _extract_named_phrases(title: str) -> set[str]:
    return {m.strip().lower() for m in _QUOTED_RE.findall(title)}


def _shared_named_phrase(title_a: str, title_b: str) -> bool:
    """Return True if a quoted phrase from either title also appears verbatim in the other."""
    a, b = title_a.lower(), title_b.lower()
    for phrase in _extract_named_phrases(title_a) | _extract_named_phrases(title_b):
        if phrase in a and phrase in b:
            return True
    return False


def _shared_actor_and_token(title_a: str, title_b: str) -> bool:
    """Return True if titles share a known threat actor AND at least one other meaningful token."""
    a, b = title_a.lower(), title_b.lower()
    for actor in THREAT_ACTORS:
        if actor in a and actor in b:
            actor_tokens = frozenset(actor.split())
            if (_token_set(title_a) - actor_tokens) & (_token_set(title_b) - actor_tokens):
                return True
    return False


async def is_duplicate(title: str, redis_client, summary: str = "") -> bool:
    """
    Returns True if the article is a duplicate (should be skipped).
    Mutates Redis state when NOT a duplicate.
    `summary` is optional but strongly recommended — used for CVE-based matching.
    """
    fp = fingerprint(title)
    text = f"{title} {summary}"
    cves = _extract_cves(text)

    # --- Layer 1: exact/near-exact fingerprint ---
    exists = await redis_client.sismember(FINGERPRINTS_KEY, fp)
    if exists:
        logger.debug(f"[Dedup L1] Fingerprint match: {title[:70]}")
        return True

    # --- Layer 1b: CVE-ID match within TTL window ---
    for cve in cves:
        if await redis_client.exists(f"{CVES_KEY}:{cve}"):
            logger.info(f"[Dedup L1b] CVE {cve} already seen: '{title[:60]}'")
            return True

    # --- Layer 2: semantic similarity vs recent 50 titles ---
    recent_raw = await redis_client.lrange(RECENT_TITLES_KEY, 0, RECENT_TITLES_MAX - 1)
    recent_titles = [t.decode() if isinstance(t, bytes) else t for t in recent_raw]

    if recent_titles:
        new_tokens = _token_set(title)

        # 2a — Entity overlap (L0) + Jaccard overlap (fast, catches proper-noun matches)
        for existing in recent_titles:
            if _temporal_conflict(title, existing):
                continue
            if _shared_named_phrase(title, existing):
                logger.info(f"[Dedup L0a] Shared named phrase duplicate: '{title[:60]}' ≈ '{existing[:60]}'")
                return True
            if _shared_actor_and_token(title, existing):
                logger.info(f"[Dedup L0b] Shared threat actor duplicate: '{title[:60]}' ≈ '{existing[:60]}'")
                return True
            pair = _shared_vendor_product(title, existing)
            if pair:
                existing_tokens = _token_set(existing)
                shared_tokens = (new_tokens - frozenset(pair.split())) & (existing_tokens - frozenset(pair.split()))
                if shared_tokens:
                    logger.info(f"[Dedup L0c] Shared vendor+product '{pair}' duplicate: '{title[:60]}' ≈ '{existing[:60]}'")
                    return True
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
    for cve in cves:
        await redis_client.set(f"{CVES_KEY}:{cve}", "1", ex=CVE_TTL)

    return False
