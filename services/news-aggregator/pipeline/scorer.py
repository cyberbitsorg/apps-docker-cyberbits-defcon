"""
Defcon score computation — 4 dimensions × 25 points = 0–100.

  1. Volume:   new articles this cycle / 12 * 25
  2. CVE:      avg CVSS scores extracted from text / 10 * 25
  3. Impact:   weighted keyword scan for breadth signals
  4. Keywords: tiered threat vocabulary scan
"""
import re
from dataclasses import dataclass

# Keyword tiers
TIER1 = ["zero-day", "zero day", "nation-state", "state-sponsored", "ransomware attack", "critical infrastructure"]
TIER2 = ["ransomware", "backdoor", "supply chain", "apt", "wiper", "botnet", "ddos", "rce", "remote code execution"]
TIER3 = ["vulnerability", "exploit", "patch", "breach", "malware", "phishing", "cve", "zero-day", "trojan", "spyware"]

SEVERITY_WORDS = {"critical": 9.0, "high": 7.0, "medium": 5.0, "low": 2.5}


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
            return 5
        elif t >= 60:
            return 4
        elif t >= 40:
            return 3
        elif t >= 20:
            return 2
        return 1

    @property
    def label(self) -> str:
        return {1: "LOW", 2: "GUARDED", 3: "ELEVATED", 4: "HIGH", 5: "CRITICAL"}[self.level]

    @property
    def color(self) -> str:
        return {
            1: "#22c55e",   # green-500
            2: "#3b82f6",   # blue-500
            3: "#f59e0b",   # amber-500
            4: "#ea580c",   # orange-600
            5: "#dc2626",   # red-600
        }[self.level]

    def to_dict(self) -> dict:
        return {
            "volume_score": round(self.volume_score, 2),
            "cve_score": round(self.cve_score, 2),
            "impact_score": round(self.impact_score, 2),
            "keyword_score": round(self.keyword_score, 2),
        }


def compute_article_score(title: str, summary: str) -> float:
    """Per-article score (0–100) for storing alongside the article."""
    text = f"{title} {summary}".lower()
    factors = _compute_factors(articles_texts=[text], new_count=1)
    return round(factors.total, 2)


def compute_global_score(articles: list[dict], new_count: int) -> DefconFactors:
    """
    Compute the global Defcon score from the sliding window of articles.
    Each article dict must have 'title' and 'summary' keys.
    """
    if not articles:
        return DefconFactors(0, 0, 0, 0)

    texts = [f"{a.get('title', '')} {a.get('summary', '')}".lower() for a in articles]
    return _compute_factors(texts, new_count)


def _compute_factors(articles_texts: list[str], new_count: int) -> DefconFactors:
    n = len(articles_texts)
    if n == 0:
        return DefconFactors(0, 0, 0, 0)

    # --- Dimension 1: Volume ---
    volume_score = min(new_count / 12, 1.0) * 25

    # --- Dimension 2: CVE Severity ---
    cvss_scores = []
    for text in articles_texts:
        for m in re.finditer(r"cvss[\s:v]*(\d+\.?\d*)", text, re.IGNORECASE):
            try:
                val = float(m.group(1))
                if 0 <= val <= 10:
                    cvss_scores.append(val)
            except ValueError:
                pass
        # Infer from severity words if no explicit score
        if not cvss_scores:
            for word, score in SEVERITY_WORDS.items():
                if re.search(rf"\b{word}\b", text):
                    cvss_scores.append(score)
                    break

    if cvss_scores:
        avg_cvss = sum(cvss_scores) / len(cvss_scores)
        cve_score = (avg_cvss / 10.0) * 25
    else:
        cve_score = 0.0

    # --- Dimension 3: Impact ---
    impact_raw = 0
    for text in articles_texts:
        if re.search(r"\d+\s*million", text):
            impact_raw += 8
        if re.search(r"power grid|hospital|water treatment|government|military|critical infrastructure", text):
            impact_raw += 7
        if re.search(r"actively exploit", text):
            impact_raw += 6
        m = re.search(r"(\d+)\s*countries", text)
        if m and int(m.group(1)) > 5:
            impact_raw += 6
        if re.search(r"data breach|leaked|exposed", text):
            impact_raw += 4
        if re.search(r"\d{6,}\s*(users|records|devices|systems)", text):
            impact_raw += 5

    impact_score = min(impact_raw / (n * 3), 1.0) * 25

    # --- Dimension 4: Keywords ---
    keyword_raw = 0
    for text in articles_texts:
        for kw in TIER1:
            if kw in text:
                keyword_raw += 5
        for kw in TIER2:
            if kw in text:
                keyword_raw += 3
        for kw in TIER3:
            if kw in text:
                keyword_raw += 1

    keyword_score = min(keyword_raw / (n * 8), 1.0) * 25

    return DefconFactors(
        volume_score=round(volume_score, 2),
        cve_score=round(cve_score, 2),
        impact_score=round(impact_score, 2),
        keyword_score=round(keyword_score, 2),
    )
