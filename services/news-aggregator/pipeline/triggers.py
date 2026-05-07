"""
Decisive trigger detection for DEFCON Track A scoring.

A "trigger" is a high-confidence pattern that alone justifies a high DEFCON score:
  - active_exploitation: vuln being exploited in the wild
  - confirmed_breach: named/scaled data breach
  - apt_campaign: nation-state / named-actor campaign with target
  - kev_addition: CISA KEV catalog update

Precedence: active_exploitation > kev_addition > confirmed_breach > apt_campaign.
"""
import re
from dataclasses import dataclass
from typing import Optional, Literal

from pipeline.vocabulary import THREAT_ACTORS, CRITICAL_SECTORS

TriggerType = Literal["active_exploitation", "confirmed_breach", "apt_campaign", "kev_addition"]

TRIGGER_BASE: dict[TriggerType, int] = {
    "active_exploitation": 80,
    "confirmed_breach": 80,
    "kev_addition": 80,
    "apt_campaign": 75,
}

# Precedence (highest first): when multiple triggers match, the first listed wins.
PRECEDENCE: tuple[TriggerType, ...] = (
    "active_exploitation",
    "kev_addition",
    "confirmed_breach",
    "apt_campaign",
)


@dataclass(frozen=True)
class TriggerMatch:
    trigger: TriggerType
    matched_text: str  # the substring that fired the trigger (for logging/UI)


# --- patterns ---

_ACTIVE_EXPLOITATION_PATTERNS = [
    r"\bactively exploited\b",
    r"\bactive exploitation\b",
    r"\bexploited(?! vulnerabilities)\b",  # match "exploited" but not when followed by "vulnerabilities"
    r"\bexploited in (the wild|attacks|the open)\b",
    r"\bin[- ]the[- ]wild\b",
    r"\bunder (active )?attack\b",
    r"\bunder exploitation\b",
    r"\b(zero[- ]day|0[- ]day) exploited\b",
    r"\bkev catalog\b",
]

_KEV_PATTERNS = [
    # CISA + (KEV or "known exploited") + (adds/added)
    r"\bcisa\b.{0,50}\b(kev|known exploited)\b.{0,50}\b(adds?|added)\b",
    r"\bcisa\b.{0,50}\b(adds?|added)\b.{0,50}\b(kev|known exploited)\b",
]

_BREACH_VERB = re.compile(
    r"\b(confirms? breach|breached|data leak|data dump|dump puts|leaked database|claims dump|stolen .{0,30}(records|users|emails|customers))\b",
    re.IGNORECASE,
)

_BREACH_SCALE_MILLIONS = re.compile(r"\bmillions? of\b", re.IGNORECASE)
_BREACH_SCALE_NUMERIC  = re.compile(r"\b\d+[kKmM]\s*(users|records|emails|accounts|customers)\b", re.IGNORECASE)

_CRITICAL_SECTOR_RE = re.compile(
    r"\b(" + "|".join(re.escape(s) for s in CRITICAL_SECTORS) + r")\b",
    re.IGNORECASE,
)

_APT_HINTS = re.compile(
    r"\b(apt|nation[- ]state|state[- ]sponsored)\b",
    re.IGNORECASE,
)

_THREAT_ACTOR_RE = re.compile(
    r"\b(" + "|".join(re.escape(a) for a in THREAT_ACTORS) + r")\b",
    re.IGNORECASE,
)

_APT_VERB = re.compile(
    r"\b(campaign|targets|targeting|espionage|breach)\b",
    re.IGNORECASE,
)


# --- detection helpers (each returns matched substring or None) ---

def _match_active_exploitation(text: str) -> Optional[str]:
    for pattern in _ACTIVE_EXPLOITATION_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return m.group(0)
    return None


def _match_kev(text: str) -> Optional[str]:
    for pattern in _KEV_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if m:
            return m.group(0)
    return None


def _match_breach(text: str) -> Optional[str]:
    verb = _BREACH_VERB.search(text)
    if not verb:
        return None
    has_scale = (
        _BREACH_SCALE_MILLIONS.search(text)
        or _BREACH_SCALE_NUMERIC.search(text)
        or _CRITICAL_SECTOR_RE.search(text)
    )
    if not has_scale:
        return None
    return verb.group(0)


def _match_apt(text: str) -> Optional[str]:
    has_hint = _APT_HINTS.search(text) or _THREAT_ACTOR_RE.search(text)
    if not has_hint:
        return None
    if not _APT_VERB.search(text):
        return None
    if not _CRITICAL_SECTOR_RE.search(text):
        # require a target/sector mention for apt_campaign — generic "apt campaign" alone is too weak
        return None
    return has_hint.group(0)


_DETECTORS = {
    "active_exploitation": _match_active_exploitation,
    "kev_addition": _match_kev,
    "confirmed_breach": _match_breach,
    "apt_campaign": _match_apt,
}


def detect_trigger(text: str) -> Optional[TriggerMatch]:
    """Return the highest-precedence trigger fired by this text, or None."""
    for trigger in PRECEDENCE:
        matched = _DETECTORS[trigger](text)
        if matched:
            return TriggerMatch(trigger=trigger, matched_text=matched)
    return None
