"""
DEFCON Scoring v2 — decisive paths + capped stacking.

Per-article: max(track_a, track_b), capped 100. Track A = trigger base + Track B bonus
capped at 20. Track B = sum of CVE/impact/keyword dimensions, capped at 75.

Global: weighted-max of article scores in last 24h, plus volume bonus, plus sticky
displayed-level state machine.
"""
import math
import re
from dataclasses import dataclass
from typing import Optional

from pipeline.vocabulary import TIER1, TIER2, TIER3, WB_REQUIRED
from pipeline.triggers import detect_trigger, TRIGGER_BASE, TriggerType


# --- shared signal helpers (v2) ---

_CVE_ID_RE = re.compile(r"\bCVE[-–— ]?\d{4}[-–— ]?\d{3,}\b", re.IGNORECASE)

_SEVERITY_WORDS = {"critical": 9.0, "high": 7.0, "medium": 5.0, "low": 2.5}


def _extract_cvss_v2(text: str) -> float:
    """
    Best CVSS score (0-10). Severity-word fallback only fires when text also
    contains a CVE id. Kills the 'critical for SOC teams' false positives.
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
    if _CVE_ID_RE.search(text):
        for word, score in _SEVERITY_WORDS.items():
            if re.search(rf"\b{word}\b", text, re.IGNORECASE):
                return score
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

    Density = raw / max(1.0, log2(token_count)). Denominator chosen so a typical
    400-token critical article saturates near 25 (log2(400) ~= 8.6, so a raw of
    ~21 yields ~22-25 after the (raw/density)/cap*25 transform). Long boilerplate
    no longer wins.
    """
    raw = _extract_keyword_raw(text)
    if raw == 0:
        return 0.0
    token_count = max(1, len(text.split()))
    denom = max(1.0, math.log2(token_count + 1))
    density = raw / denom
    # cap density at ~3.0 (calibrated so dense critical articles reach 25)
    DENSITY_CAP = 3.0
    return min(density / DENSITY_CAP, 1.0) * 25.0


@dataclass(frozen=True)
class ArticleScore:
    score: float
    trigger: Optional[TriggerType]
    track_a: float  # Track A score (0 if no trigger)
    track_b: float  # Track B final (capped at 75)


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
    track_b_unclamped = cve + impact + kw
    track_b_final = min(track_b_unclamped, 75.0)

    trigger_match = detect_trigger(text)
    if trigger_match is not None:
        base = TRIGGER_BASE[trigger_match.trigger]
        bonus = min(track_b_unclamped, 20.0)
        track_a = min(base + bonus, 100.0)
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
