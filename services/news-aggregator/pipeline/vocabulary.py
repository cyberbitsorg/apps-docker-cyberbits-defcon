"""
Threat vocabulary for DEFCON scoring.

TIER1/2/3 = keyword lists weighted at 8/4/1 points each in Track B keyword scoring.
THREAT_ACTORS = named groups used by triggers.py for named-actor detection.
CRITICAL_SECTORS = regex-safe sector names used by impact + breach trigger.
KNOWN_STEALERS = stealer/RAT family names used by malware_campaign trigger.
WB_REQUIRED = short tokens that need word-boundary matching to avoid false positives.
"""

TIER1 = [
    "zero-day", "zero day", "0-day", "0day", "0 day",
    "nation-state", "nation state",
    "state-sponsored", "state sponsored",
    "ransomware attack", "critical infrastructure",
    "infostealer", "stealer campaign", "malware campaign",
    "supply chain attack", "credential stealer",
    "malicious extension", "malicious plugin",
    "malicious package", "malicious dependency",
]

TIER2 = [
    "ransomware", "backdoor", "back door", "supply chain", "apt", "wiper",
    "botnet", "ddos", "rce", "remote code execution",
    "rootkit", "privilege escalation", "local privilege escalation",
    "root access", "root privileges", "root shell",
    "lateral movement", "vishing", "smishing", "credential stuffing",
    "session hijacking", "account takeover",
    "data exfiltration", "exfiltrate", "exfiltration",
    "hijack", "hijacking",
    "bypass authentication", "authentication bypass", "authorization bypass",
    "stealer", "info-stealer", "credential theft", "credential harvesting",
    "clickfix", "loader", "dropper", "keylogger", "rat",
    "route to root", "compromised", "compromise", "infect", "infecting",
]

TIER3 = [
    "vulnerability", "exploit", "patch", "breach", "malware",
    "phishing", "cve", "trojan", "spyware",
    "data leak", "threat actor", "unauthorized access", "credential",
    "dump", "database leak", "vendor advisory", "incident response",
    "extortion",
    "campaign", "targeting", "payload",
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
    "university", "universities", "college", "colleges", "educational",
    "rail", "railway", "metro", "transit", "subway",
    "school", "schools", "k-12",
    "hospital system", "health system", "healthcare",
    "package registry",
]

# Known infostealer/RAT family names — used by malware_campaign trigger only.
# Not part of Track B keyword scoring (avoids per-name boilerplate accumulation).
KNOWN_STEALERS = [
    "amos", "redline", "lumma", "vidar", "atomic stealer", "shub",
    "metastealer", "stealc", "raccoon",
]

# Short terms that appear as substrings in unrelated words ("rce" in "force",
# "apt" in "capture", "rat" in "rate", "celebrate", etc.) and the numeric
# "0-day" spellings, which must not match "10-day trial" / "10 day forecast".
WB_REQUIRED = frozenset({"rce", "apt", "rat", "0-day", "0day", "0 day"})
