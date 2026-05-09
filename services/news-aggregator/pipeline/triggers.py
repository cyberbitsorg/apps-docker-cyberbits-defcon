"""
Decisive trigger detection for DEFCON Track A scoring.

A "trigger" is a high-confidence pattern that alone justifies an elevated DEFCON score:
  - active_exploitation: vuln being exploited in the wild
  - kev_addition: CISA KEV catalog update
  - critical_scope_vuln: vuln keyword + broad scope amplifier
  - confirmed_breach: named/scaled data breach
  - apt_campaign: nation-state / named-actor campaign with target
  - malware_campaign: stealer/loader/RAT or known stealer name + campaign verb

Precedence (highest first): active_exploitation > kev_addition > critical_scope_vuln
  > confirmed_breach > apt_campaign > malware_campaign.
"""
import re
from dataclasses import dataclass
from typing import Optional, Literal

from pipeline.vocabulary import THREAT_ACTORS, CRITICAL_SECTORS, KNOWN_STEALERS

TriggerType = Literal[
    "active_exploitation", "confirmed_breach", "apt_campaign",
    "kev_addition", "critical_scope_vuln", "malware_campaign",
]

TRIGGER_BASE: dict[TriggerType, int] = {
    "active_exploitation": 80,
    "kev_addition": 75,
    "critical_scope_vuln": 70,
    "confirmed_breach": 70,
    "apt_campaign": 65,
    "malware_campaign": 60,
}

# Precedence (highest first): when multiple triggers match, the first listed wins.
PRECEDENCE: tuple[TriggerType, ...] = (
    "active_exploitation",
    "kev_addition",
    "critical_scope_vuln",
    "confirmed_breach",
    "apt_campaign",
    "malware_campaign",
)


@dataclass(frozen=True)
class TriggerMatch:
    trigger: TriggerType
    matched_text: str  # the substring that fired the trigger (for logging/UI)


# --- patterns ---

_ACTIVE_EXPLOITATION_PATTERNS = [
    r"\bactively exploited\b",
    r"\bactive exploitation\b",
    r"\bexploited in (the wild|attacks?|the open)\b",
    r"\bin[- ]the[- ]wild\b",
    r"\bunder (active )?attack\b",
    r"\bunder exploitation\b",
    r"\b(zero[- ]day|0[- ]day) exploited\b",
    r"\bexploits?\s+(cve|known|critical|vuln|flaw|bug|zero[- ]?day)",
    r"\bexploited\s+as\s+a?\s*(zero|0)[- ]?day\b",
    r"\bweaponized\b",
    r"\b(actively\s+)?exploiting\b",
]

_KEV_PATTERNS = [
    # CISA + (KEV or "known exploited") + (adds/added)
    r"\bcisa\b.{0,50}\b(kev|known exploited)\b.{0,50}\b(adds?|added)\b",
    r"\bcisa\b.{0,50}\b(adds?|added)\b.{0,50}\b(kev|known exploited)\b",
    r"\bkev catalog\b",
]

_BREACH_VERB = re.compile(
    r"\b(confirms? breach|breached|data leak|data dump|dump puts|leaked database|claims dump|"
    r"(stolen|stole|theft of|claimed theft of|stealing) .{0,40}(records|users|emails|customers|accounts|tokens|credentials))\b",
    re.IGNORECASE,
)

_BREACH_SCALE_MILLIONS = re.compile(r"\bmillions? of\b", re.IGNORECASE)
_BREACH_SCALE_NUMERIC  = re.compile(r"\b\d+[kKmM]\+?\s*(users|records|emails|accounts|customers)\b", re.IGNORECASE)

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

_APT_BREACH_VERB = re.compile(
    r"\b(breach|breached|theft|stole|stolen|leak|leaked|hack|hacked|compromise|compromised|exfiltrat\w+)\b",
    re.IGNORECASE,
)

_SCOPE_AMPLIFIER_PATTERNS = [
    r"\b(all|most)\s+major\s+(linux|windows|macos|android|ios|distros?|distributions?|systems?|platforms?|versions?|releases?)\b",
    r"\bevery\s+(version|release)\b",
    r"\bbillions?\s+of\s+(devices|users)\b",
    r"\bany\s+(linux|windows|macos|android|ios)\b",
]

_SCOPE_AMPLIFIER_RE = re.compile("|".join(_SCOPE_AMPLIFIER_PATTERNS), re.IGNORECASE)


def _has_scope_amplifier(text: str) -> bool:
    """True if text describes broad-scope impact (entire OS family, billions of users, etc.)."""
    return _SCOPE_AMPLIFIER_RE.search(text) is not None


_NEWSLETTER_TITLE_RE = re.compile(
    r"\bnewsletter\b|\bround\s+\d+\b|\bweekly\s+(roundup|recap|digest)\b|\bweek in (review|security)\b",
    re.IGNORECASE,
)


def _is_newsletter_title(title: str) -> bool:
    """Aggregator-style titles (weekly newsletter, round-up) should not fire decisive triggers."""
    return _NEWSLETTER_TITLE_RE.search(title) is not None


# --- detection helpers (each returns matched substring or None) ---

_NEGATION_WORDS_RE = re.compile(
    r"\b(no|never|not|without|unsuccessful|fails?|failed|prevent(?:ed|s)?|denied|blocked)\b",
    re.IGNORECASE,
)


def _is_negated(text: str, match_start: int, match_end: int = -1) -> bool:
    """True if the 30 chars preceding match_start (or 60 chars after match_end) contain a negation marker."""
    window_start = max(0, match_start - 30)
    if _NEGATION_WORDS_RE.search(text[window_start:match_start]) is not None:
        return True
    if match_end >= 0:
        window_end = min(len(text), match_end + 60)
        if _NEGATION_WORDS_RE.search(text[match_end:window_end]) is not None:
            return True
    return False


def _match_active_exploitation(text: str) -> Optional[str]:
    for pattern in _ACTIVE_EXPLOITATION_PATTERNS:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            if not _is_negated(text, m.start(), m.end()):
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
    if not (_CRITICAL_SECTOR_RE.search(text) or _APT_BREACH_VERB.search(text)):
        # require a target/sector mention OR a breach/theft verb — generic actor mention alone is too weak
        return None
    return has_hint.group(0)


_VULN_KEYWORD_RE = re.compile(
    r"\b(zero[- ]?day|0[- ]?day|RCE|remote code execution|privilege escalation|unauthenticated)\b",
    re.IGNORECASE,
)


def _match_critical_scope_vuln(text: str) -> Optional[str]:
    vuln = _VULN_KEYWORD_RE.search(text)
    if not vuln:
        return None
    if not _has_scope_amplifier(text):
        return None
    return vuln.group(0)


_MALWARE_NOUN_RE = re.compile(
    r"\b(stealer|infostealer|info-stealer|loader|dropper|keylogger|rat)\b",
    re.IGNORECASE,
)

_KNOWN_STEALER_RE = re.compile(
    r"\b(" + "|".join(re.escape(s) for s in KNOWN_STEALERS) + r")\b",
    re.IGNORECASE,
)

_CAMPAIGN_VERB_RE = re.compile(
    r"\b(targeting|deploys?|distributes?|spreads?|drops?|delivers?|campaign)\b",
    re.IGNORECASE,
)


def _match_malware_campaign(text: str) -> Optional[str]:
    noun = _MALWARE_NOUN_RE.search(text) or _KNOWN_STEALER_RE.search(text)
    if not noun:
        return None
    if not _CAMPAIGN_VERB_RE.search(text):
        return None
    return noun.group(0)


_DETECTORS = {
    "active_exploitation": _match_active_exploitation,
    "kev_addition": _match_kev,
    "confirmed_breach": _match_breach,
    "apt_campaign": _match_apt,
    "critical_scope_vuln": _match_critical_scope_vuln,
    "malware_campaign": _match_malware_campaign,
}


def detect_trigger(text: str) -> Optional[TriggerMatch]:
    """Return the highest-precedence trigger fired by this text, or None."""
    for trigger in PRECEDENCE:
        matched = _DETECTORS[trigger](text)
        if matched:
            return TriggerMatch(trigger=trigger, matched_text=matched)
    return None
