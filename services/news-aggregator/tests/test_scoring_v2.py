import pytest
from pipeline.scoring_v2 import (
    _extract_cvss_v2,
    _extract_impact_raw_v2,
    _extract_keyword_score_normalized,
    compute_article_score_v2,
    ArticleScore,
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


def test_article_v2_palo_alto_zero_day():
    score = compute_article_score_v2(
        "Palo Alto firewall RCE zero-day exploited in attacks",
        "vendor confirms active exploitation in the wild against PAN-OS",
    )
    assert score.score >= 85
    assert score.trigger == "active_exploitation"


def test_article_v2_breach_with_scale():
    score = compute_article_score_v2(
        "Hospital patient records breach confirmed",
        "vendor confirms breach affecting hospital systems with millions of records exposed",
    )
    assert score.score >= 80
    assert score.trigger == "confirmed_breach"


def test_article_v2_routine_patch_track_b_only():
    score = compute_article_score_v2(
        "Microsoft patches medium severity CVE-2024-1234",
        "monthly update fixes vulnerability with cvss 5.0",
    )
    assert score.score < 40
    assert score.trigger is None


def test_article_v2_track_b_capped_at_75():
    # very keyword-heavy article with no Track A trigger should still cap at 75
    score = compute_article_score_v2(
        "keyword dense text without trigger",
        "rce ddos backdoor exploit malware breach cve trojan spyware data leak threat actor unauthorized access credential dumped database vendor advisory incident response",
    )
    # Track A "active_exploitation" did NOT fire here (no exploited/wild text), so Track B path
    # If trigger fires (e.g., zero-day exploited variant), allow >75
    if score.trigger is None:
        assert score.score <= 75
    else:
        assert score.score >= 75


def test_article_v2_empty_returns_zero():
    score = compute_article_score_v2("", "")
    assert score.score == 0.0
    assert score.trigger is None


def test_article_v2_track_a_with_track_b_bonus():
    # Active exploitation + critical sector + millions → Track A base + bonus
    score = compute_article_score_v2(
        "Hospital systems actively exploited via zero-day",
        "millions of patient records affected; cvss 9.8 critical infrastructure under active attack",
    )
    assert score.score >= 95
    assert score.trigger == "active_exploitation"


def test_article_v2_returns_dataclass_with_fields():
    s = compute_article_score_v2("routine patch", "minor")
    assert hasattr(s, "score")
    assert hasattr(s, "trigger")
    assert hasattr(s, "track_a")
    assert hasattr(s, "track_b")
