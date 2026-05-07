from pipeline.vocabulary import (
    TIER1, TIER2, TIER3,
    THREAT_ACTORS,
    CRITICAL_SECTORS,
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
