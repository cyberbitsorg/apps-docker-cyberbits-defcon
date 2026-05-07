import pytest
from pipeline.scoring_v2 import (
    _extract_cvss_v2,
    _extract_impact_raw_v2,
    _extract_keyword_score_normalized,
)


# --- _extract_cvss_v2: severity-word fallback gated by CVE id ---

def test_cvss_explicit_score_wins():
    assert _extract_cvss_v2("cvss 9.8 vulnerability") == pytest.approx(9.8)


def test_cvss_severity_word_alone_does_not_score():
    # "critical" without a CVE id should NOT score
    assert _extract_cvss_v2("critical for soc teams to patch") == 0.0


def test_cvss_severity_word_with_cve_id_scores():
    assert _extract_cvss_v2("critical cve-2026-1234 fixed") == 9.0


def test_cvss_high_severity_with_cve():
    assert _extract_cvss_v2("high severity cve-2026-9999 disclosed") == 7.0


def test_cvss_explicit_overrides_severity_word():
    assert _extract_cvss_v2("cvss 6.5 critical cve-2026-1234") == pytest.approx(6.5)


# --- _extract_impact_raw_v2: actively exploited removed (now Track A trigger) ---

def test_impact_v2_no_actively_exploited_clause():
    # "actively exploited" is now Track A only — should NOT score in Track B impact
    assert _extract_impact_raw_v2("actively exploited bug") == 0


def test_impact_v2_critical_sector_still_scores():
    assert _extract_impact_raw_v2("hospital systems hit") == 5


def test_impact_v2_millions_still_scores():
    assert _extract_impact_raw_v2("affects millions of users") == 4


def test_impact_v2_data_breach_still_scores():
    assert _extract_impact_raw_v2("data breach exposed credentials") == 3


# --- _extract_keyword_score_normalized: length normalization ---

def test_keyword_short_text_unaffected():
    # short text — no significant denominator effect
    score_short = _extract_keyword_score_normalized("ransomware attack")
    assert score_short > 0


def test_keyword_long_padded_does_not_outscore_dense():
    # same keyword content, one padded with non-keyword filler
    short = "zero-day exploit"
    long = short + " " + " ".join(["lorem"] * 200)
    score_short = _extract_keyword_score_normalized(short)
    score_long  = _extract_keyword_score_normalized(long)
    # length normalization: long should NOT score noticeably higher than short
    assert score_long <= score_short + 1.0


def test_keyword_caps_at_25():
    # extremely keyword-dense text should still cap at 25
    text = "zero-day nation-state ransomware attack critical infrastructure rce ddos backdoor exploit malware breach cve"
    assert _extract_keyword_score_normalized(text) <= 25.0
