from pipeline.vocabulary import (
    TIER1, TIER2, TIER3,
    THREAT_ACTORS,
    CRITICAL_SECTORS,
    KNOWN_STEALERS,
    WB_REQUIRED,
)


def test_tier1_contains_existing_keywords():
    for kw in ["zero-day", "nation-state", "ransomware attack", "critical infrastructure"]:
        assert kw in TIER1


def test_tier2_contains_new_keywords():
    for kw in ["vishing", "smishing", "back door", "credential stuffing"]:
        assert kw in TIER2


def test_threat_actors_includes_common_groups():
    for actor in ["shinyhunters", "lockbit", "lazarus", "muddywater", "scattered spider"]:
        assert actor in THREAT_ACTORS


def test_threat_actors_lowercase():
    assert all(a == a.lower() for a in THREAT_ACTORS)


def test_critical_sectors_is_regex_safe_list():
    assert "power grid" in CRITICAL_SECTORS
    assert "hospital" in CRITICAL_SECTORS


def test_wb_required_includes_short_ambiguous_terms():
    assert "rce" in WB_REQUIRED
    assert "apt" in WB_REQUIRED


def test_zero_day_not_in_tier3():
    assert "zero-day" not in TIER3
    assert "zero day" not in TIER3


def test_tier1_has_v21_additions():
    for kw in ("infostealer", "stealer campaign", "malware campaign"):
        assert kw in TIER1, f"TIER1 missing {kw!r}"


def test_tier2_has_v21_additions():
    expected = {
        "stealer", "info-stealer", "credential theft", "credential harvesting",
        "clickfix", "loader", "dropper", "keylogger", "rat",
    }
    missing = expected - set(TIER2)
    assert not missing, f"TIER2 missing {missing}"


def test_tier3_has_v21_additions():
    for kw in ("campaign", "targeting", "payload"):
        assert kw in TIER3, f"TIER3 missing {kw!r}"


def test_known_stealers_lowercase():
    assert KNOWN_STEALERS, "KNOWN_STEALERS empty"
    for name in KNOWN_STEALERS:
        assert name == name.lower(), f"{name!r} not lowercase"


def test_known_stealers_includes_common_families():
    for name in ("amos", "redline", "lumma", "vidar", "stealc"):
        assert name in KNOWN_STEALERS, f"{name!r} missing"


def test_wb_required_includes_rat():
    assert "rat" in WB_REQUIRED


def test_tier1_has_v23_additions():
    for kw in ("supply chain attack", "credential stealer"):
        assert kw in TIER1


def test_tier2_has_v23_additions():
    for kw in ("route to root", "compromised", "compromise", "infect", "infecting"):
        assert kw in TIER2


def test_malicious_extension_in_tier1():
    assert "malicious extension" in TIER1


def test_malicious_plugin_in_tier1():
    assert "malicious plugin" in TIER1


def test_malicious_package_in_tier1():
    assert "malicious package" in TIER1


def test_malicious_dependency_in_tier1():
    assert "malicious dependency" in TIER1


def test_package_registry_in_critical_sectors():
    assert "package registry" in CRITICAL_SECTORS
