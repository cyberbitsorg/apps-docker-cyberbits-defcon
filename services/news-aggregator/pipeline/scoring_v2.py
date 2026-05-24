"""
DEFCON Scoring v2 — decisive paths + capped stacking.

Per-article: max(track_a, track_b), capped 100. Track A = trigger base + Track B bonus
capped at 10. Track B = sum of CVE/impact/keyword dimensions, capped at 80.

Global: weighted-max of article scores in last 24h, plus volume bonus, plus sticky
displayed-level state machine.
"""
import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from pipeline.vocabulary import TIER1, TIER2, TIER3, WB_REQUIRED
from pipeline.triggers import detect_trigger, TRIGGER_BASE, TriggerType, _has_scope_amplifier, _is_newsletter_title


# --- shared signal helpers (v2) ---

_CVE_ID_RE = re.compile(r"\bCVE[-–— ]?\d{4}[-–— ]?\d{3,}\b", re.IGNORECASE)

_SEVERITY_WORDS = {"critical": 9.0, "high": 7.0, "medium": 5.0, "low": 2.5}


def _extract_cvss_v2(text: str) -> float:
    """
    Best CVSS score (0-10).

    1. Explicit "cvss <number>" within 50-char window wins.
    2. Otherwise, severity word + CVE id co-occurrence maps to a default score.
    3. Otherwise, prose-described vulnerability with strong scope/qualifier
       infers a score (mirrors how a human reads severity from a feed summary
       that omits CVSS). Returns 0.0 if none apply.
    """
    scores = []
    for context_match in re.finditer(r"cvss[^\n]{0,50}", text, re.IGNORECASE):
        context = context_match.group(0)
        for num_match in re.finditer(r"(?<![.\w])(\d+\.?\d*)(?!\w)", context):
            try:
                val = float(num_match.group(1))
                if 0.0 <= val <= 10.0:
                    scores.append(val)
            except ValueError:
                pass
    if scores:
        return max(scores)

    # "max severity" / "maximum severity" — vendor-press shorthand for CVSS ~10.
    if re.search(r"\bmax(?:imum)?\s+severity\b", text, re.IGNORECASE):
        return 9.0

    if _CVE_ID_RE.search(text):
        matching = [score for word, score in _SEVERITY_WORDS.items()
                    if re.search(rf"\b{word}\b", text, re.IGNORECASE)]
        if matching:
            return max(matching)

    # Tertiary: prose-described vulnerabilities with strong scope/qualifier.
    has_scope = _has_scope_amplifier(text)
    if re.search(r"\bzero[- ]?day\b", text, re.IGNORECASE) and has_scope:
        return 8.0
    if re.search(r"\b(remote code execution|RCE)\b", text, re.IGNORECASE) and (
        re.search(r"\bunauthenticated\b", text, re.IGNORECASE) or has_scope
    ):
        return 8.0
    if re.search(r"\b(root|kernel)\b", text, re.IGNORECASE) and has_scope:
        return 7.5

    return 0.0


def _extract_impact_raw_v2(text: str) -> int:
    """Track B impact signals. 'actively exploited' removed — that is now a Track A trigger."""
    raw = 0
    if re.search(r"power grid|hospital|water treatment|government|military|critical infrastructure", text, re.IGNORECASE):
        raw += 5
    if re.search(r"(?:\d[\d,.]*\s*)?millions?\b", text, re.IGNORECASE):
        raw += 4
    m = re.search(r"(\d+)\s*countries", text, re.IGNORECASE)
    if m and int(m.group(1)) > 5:
        raw += 4
    if re.search(r"data breach|breached|breaches|\bbreach\b|leaked|exposed|exposing", text, re.IGNORECASE):
        raw += 3
    if re.search(r"(?:\d{6,}|\d{3,}[kK])\s*(users|records|devices|systems)", text, re.IGNORECASE):
        raw += 3
    if re.search(r"hundreds of\s+(colleges?|universities|schools|organizations|companies|agencies)", text, re.IGNORECASE):
        raw += 3
    if re.search(r"\b(all|most)\s+(major|popular|common)\s+(linux|windows|macos|android|ios|mobile\s+)?(distributions?|versions?|systems?|platforms?|devices?|distros?)\b", text, re.IGNORECASE):
        raw += 3
    if re.search(r"\bbillions?\s+of\s+(devices|users)\b", text, re.IGNORECASE):
        raw += 5
    if re.search(r"\bevery\s+(version|release)\b", text, re.IGNORECASE):
        raw += 4
    if re.search(r"\bany\s+(linux|windows|macos|android|ios)\s+(system|device|user)\b", text, re.IGNORECASE):
        raw += 4
    return raw


_IMPACT_CAP = 12  # rebalanced for v2 (was 15 with the removed actively-exploited clause)


def _extract_impact_score_v2(text: str) -> float:
    """Impact dimension scaled to 0-25."""
    return min(_extract_impact_raw_v2(text) / _IMPACT_CAP, 1.0) * 25.0


def _extract_keyword_raw(text: str) -> int:
    """Raw weighted keyword count from tier vocabulary (TIER1=8, TIER2=4, TIER3=1)."""
    raw = 0
    for tier, pts in ((TIER1, 8), (TIER2, 4), (TIER3, 1)):
        for kw in tier:
            if kw in WB_REQUIRED:
                if re.search(r"\b" + re.escape(kw) + r"\b", text, re.IGNORECASE):
                    raw += pts
            else:
                if kw.lower() in text.lower():
                    raw += pts
    return raw


def _extract_keyword_score_normalized(text: str) -> float:
    """
    Length-normalized keyword score, scaled to 0-25.

    Density = raw / max(1.0, log2(token_count + 1)). A typical 400-token article
    with raw ≈ 52 saturates near 25 (log2(401) ≈ 8.65, density ≈ 6.0 → cap 2.0 → score ≈ 25).
    Long boilerplate no longer wins. Density cap reduced to 2.0 for tighter keyword control.
    """
    raw = _extract_keyword_raw(text)
    if raw == 0:
        return 0.0
    token_count = max(1, len(text.split()))
    denom = max(1.0, math.log2(token_count + 1))
    density = raw / denom
    # cap density at ~2.0 (calibrated so dense critical articles reach 25)
    DENSITY_CAP = 2.0
    return min(density / DENSITY_CAP, 1.0) * 25.0


@dataclass(frozen=True)
class ArticleScore:
    score: float
    trigger: Optional[TriggerType]
    track_a: float  # Track A score (0 if no trigger)
    track_b: float  # Track B final (capped at 80)


def _compute_track_b_unclamped(text: str) -> tuple[float, float, float]:
    """Return (cve, impact, keywords) dimension scores — pre-cap."""
    cve_raw     = _extract_cvss_v2(text)
    cve_score   = (cve_raw / 10.0) * 30.0
    impact_score = _extract_impact_score_v2(text)
    keyword_score = _extract_keyword_score_normalized(text)
    return cve_score, impact_score, keyword_score


def compute_article_score_v2(title: str, summary: str) -> ArticleScore:
    text = f"{title} {summary}".lower()
    if not text.strip():
        return ArticleScore(score=0.0, trigger=None, track_a=0.0, track_b=0.0)

    cve, impact, kw = _compute_track_b_unclamped(text)

    # Title keyword bonus — additive to Track B total so it stacks with body keywords
    # rather than being capped inside the keyword dimension (max 25).
    # Boost cap increased from 12 to 20 for stronger title emphasis.
    title_kw_raw = _extract_keyword_raw(title.lower())
    title_kw_boost = min(title_kw_raw / 8.0, 1.0) * 20.0

    track_b_unclamped = cve + impact + kw + title_kw_boost
    track_b_final = min(track_b_unclamped, 80.0)

    trigger_match = detect_trigger(text)
    if trigger_match is not None and _is_newsletter_title(title):
        trigger_match = None
    if trigger_match is not None:
        base = TRIGGER_BASE[trigger_match.trigger]
        bonus = min(track_b_unclamped, 10.0)
        track_a = min(base + bonus, 100.0)
        # With bonus cap 10: malware_campaign max = 60+10 = 70, kev_addition max = 75+10 = 85,
        # active_exploitation max = 80+10 = 90 (before 100 clamp). Track B can still reach 80,
        # so max() is load-bearing when Track B exceeds Track A (e.g. rich body, no trigger base).
        final = max(track_a, track_b_final)
        return ArticleScore(
            score=round(final, 2),
            trigger=trigger_match.trigger,
            track_a=round(track_a, 2),
            track_b=round(track_b_final, 2),
        )

    return ArticleScore(
        score=round(track_b_final, 2),
        trigger=None,
        track_a=0.0,
        track_b=round(track_b_final, 2),
    )


@dataclass(frozen=True)
class GlobalScore:
    score: float
    weighted_max: float
    volume_bonus: float
    trigger: Optional[TriggerType]
    trigger_article_id: Optional[str]
    trigger_article_title: Optional[str]


_WINDOW_HOURS = 24.0
_WINDOW_HOURS_WEEKDAY = 48.0
_WINDOW_HOURS_WEEKEND = 72.0


def _current_window_hours(now: datetime) -> float:
    """Return the active decay window in hours. 72h on Sat/Sun (UTC), 48h otherwise."""
    return _WINDOW_HOURS_WEEKEND if now.weekday() in (5, 6) else _WINDOW_HOURS_WEEKDAY


_VOLUME_BONUS_CAP = 10.0


def _age_hours(published_at: datetime) -> float:
    now = datetime.now(timezone.utc)
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)
    return (now - published_at).total_seconds() / 3600.0


def compute_global_score_v2(
    articles_in_window: list[dict],
    new_count: int,
    baseline: Optional[float],
) -> GlobalScore:
    """
    Global v2 score = clamp(weighted_max + volume_bonus, 0, 100).

    Each article in `articles_in_window` must have:
      id, title, defcon_score, defcon_trigger, published_at (datetime, tz-aware preferred).
    """
    weighted_max = 0.0
    winner: Optional[dict] = None
    for art in articles_in_window:
        weight = max(0.0, 1.0 - _age_hours(art["published_at"]) / _WINDOW_HOURS)
        contribution = float(art["defcon_score"]) * weight
        if contribution > weighted_max:
            weighted_max = contribution
            winner = art

    if baseline is None or baseline <= 0:
        volume_bonus = 0.0
    else:
        ratio = new_count / baseline
        volume_bonus = max(0.0, min((ratio - 1.0) * 10.0, _VOLUME_BONUS_CAP))

    total = min(weighted_max + volume_bonus, 100.0)

    return GlobalScore(
        score=round(total, 2),
        weighted_max=round(weighted_max, 2),
        volume_bonus=round(volume_bonus, 2),
        trigger=winner["defcon_trigger"] if winner else None,
        trigger_article_id=str(winner["id"]) if winner else None,
        trigger_article_title=winner["title"] if winner else None,
    )
