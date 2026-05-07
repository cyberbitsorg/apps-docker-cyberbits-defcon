"""
Threat vocabulary for DEFCON scoring.

TIER1/2/3 = keyword lists weighted at 8/4/1 points each in Track B keyword scoring.
THREAT_ACTORS = named groups, included in TIER2 by membership.
CRITICAL_SECTORS = regex-safe sector names used by impact + breach trigger.
WB_REQUIRED = short tokens that need word-boundary matching to avoid false positives.
"""

TIER1 = [
    "zero-day", "zero day", "nation-state", "nation state",
    "state-sponsored", "state sponsored",
    "ransomware attack", "critical infrastructure",
]

TIER2 = [
    "ransomware", "backdoor", "back door", "supply chain", "apt", "wiper",
    "botnet", "ddos", "rce", "remote code execution",
    "rootkit", "privilege escalation", "lateral movement",
    "vishing", "smishing", "credential stuffing",
    "session hijacking", "account takeover",
]

TIER3 = [
    "vulnerability", "exploit", "patch", "breach", "malware",
    "phishing", "cve", "trojan", "spyware",
    "data leak", "threat actor", "unauthorized access", "credential",
    "dump", "database leak", "vendor advisory", "incident response",
    "extortion",
]
# "zero-day" intentionally absent from TIER3 — already scored via TIER1

THREAT_ACTORS = [
    "shinyhunters", "lockbit", "cl0p", "qilin", "alphv", "blackcat", "scattered spider",
    "lazarus", "muddywater", "apt28", "apt29", "volt typhoon", "salt typhoon",
    "fancy bear", "cozy bear", "kimsuky",
]

CRITICAL_SECTORS = [
    "power grid", "hospital", "water treatment", "government", "military",
    "critical infrastructure", "airline", "bank", "financial",
]

# Short terms that appear as substrings in unrelated words ("rce" in "force", "apt" in "capture")
WB_REQUIRED = frozenset({"rce", "apt"})
