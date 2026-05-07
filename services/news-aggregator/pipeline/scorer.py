"""
Defcon score computation.

Per-article:  3 dimensions × 33.3 pts = 0-100  (CVE severity, impact, keywords)
Global:       4 dimensions × 25 pts  = 0-100  (volume spike, CVE avg, impact avg, keyword avg)
"""
import re
from dataclasses import dataclass

from pipeline.vocabulary import TIER1, TIER2, TIER3, WB_REQUIRED as _WB_REQUIRED

SEVERITY_WORDS = {"critical": 9.0, "high": 7.0, "medium": 5.0, "low": 2.5}

_IMPACT_CAP = 15
_KEYWORD_CAP = 20


@dataclass
class DefconFactors:
    volume_score: float
    cve_score: float
    impact_score: float
    keyword_score: float

    @property
    def total(self) -> float:
        return min(self.volume_score + self.cve_score + self.impact_score + self.keyword_score, 100.0)

    @property
    def level(self) -> int:
        t = self.total
        if t >= 80:
            return 1
        elif t >= 60:
            return 2
        elif t >= 40:
            return 3
        elif t >= 20:
            return 4
        return 5

    @property
    def label(self) -> str:
        return {
            1: "Cocked Pistol",
            2: "Fast Pace",
            3: "Round House",
            4: "Double Take",
            5: "Fade Out",
        }[self.level]

    @property
    def color(self) -> str:
        return {
            1: "#ffffff",
            2: "#dc2626",
            3: "#eab308",
            4: "#22c55e",
            5: "#3b82f6",
        }[self.level]

    def to_dict(self) -> dict:
        return {
            "volume_score": round(self.volume_score, 2),
            "cve_score": round(self.cve_score, 2),
            "impact_score": round(self.impact_score, 2),
            "keyword_score": round(self.keyword_score, 2),
        }


def _extract_cvss(text: str) -> float:
    """Best CVSS score from text (0-10), or inferred from severity keywords, or 0."""
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
    for word, score in SEVERITY_WORDS.items():
        if re.search(rf"\b{word}\b", text):
            return score
    return 0.0


def _extract_impact_raw(text: str) -> int:
    """Raw impact points from scale signals in article text."""
    raw = 0
    if re.search(r"actively exploit", text):
        raw += 6
    if re.search(r"power grid|hospital|water treatment|government|military|critical infrastructure", text):
        raw += 5
    if re.search(r"(?:\d[\d,.]*\s*)?millions?\b", text):
        raw += 4
    m = re.search(r"(\d+)\s*countries", text)
    if m and int(m.group(1)) > 5:
        raw += 4
    if re.search(r"data breach|breached|breaches|\bbreach\b|leaked|exposed|exposing", text):
        raw += 3
    if re.search(r"(?:\d{6,}|\d{3,}[kK])\s*(users|records|devices|systems)", text):
        raw += 3
    return raw


def _extract_keyword_raw(text: str) -> int:
    """Weighted keyword score from tiered threat vocabulary."""
    raw = 0
    for tier, pts in ((TIER1, 8), (TIER2, 4), (TIER3, 1)):
        for kw in tier:
            if kw in _WB_REQUIRED:
                if re.search(r"\b" + re.escape(kw) + r"\b", text):
                    raw += pts
            else:
                if kw in text:
                    raw += pts
    return raw


def compute_article_score(title: str, summary: str) -> float:
    """Per-article score (0-100). Three content dimensions, no volume."""
    text = f"{title} {summary}".lower()
    cve_score     = (_extract_cvss(text) / 10.0) * 33.3
    impact_score  = min(_extract_impact_raw(text) / _IMPACT_CAP, 1.0) * 33.3
    keyword_score = min(_extract_keyword_raw(text) / _KEYWORD_CAP, 1.0) * 33.3
    return round(min(cve_score + impact_score + keyword_score, 100.0), 2)


def compute_global_score(
    articles: list[dict],
    new_count: int,
    avg_volume: float | None = None,
) -> DefconFactors:
    """
    Global DEFCON score from the sliding window of recent articles.
    Each article dict must have 'title' and 'summary' keys.
    avg_volume: rolling baseline from get_volume_baseline(); None = cold start (neutral 12.5).
    """
    if not articles:
        return DefconFactors(0.0, 0.0, 0.0, 0.0)

    # Volume: relative spike vs rolling baseline
    if avg_volume is None or avg_volume == 0:
        volume_score = 12.5
    else:
        volume_score = min(new_count / avg_volume / 2.0, 1.0) * 25.0

    # Content dimensions: average each signal across the article window
    texts = [f"{a.get('title', '')} {a.get('summary', '')}".lower() for a in articles]
    n = len(texts)

    avg_cvss     = sum(_extract_cvss(t) for t in texts) / n
    avg_impact   = sum(_extract_impact_raw(t) for t in texts) / n
    avg_keywords = sum(_extract_keyword_raw(t) for t in texts) / n

    cve_score     = (avg_cvss / 10.0) * 25.0
    impact_score  = min(avg_impact / _IMPACT_CAP, 1.0) * 25.0
    keyword_score = min(avg_keywords / _KEYWORD_CAP, 1.0) * 25.0

    return DefconFactors(
        volume_score=round(volume_score, 2),
        cve_score=round(cve_score, 2),
        impact_score=round(impact_score, 2),
        keyword_score=round(keyword_score, 2),
    )
