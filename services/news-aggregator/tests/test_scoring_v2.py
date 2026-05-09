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


def test_article_v2_track_b_capped_at_80():
    # Saturate cve + impact + keyword + title boost; track_b must cap at 80.
    title = "ransomware zero-day rce backdoor critical"
    summary = (
        "cvss 10.0 ransomware zero-day rce backdoor critical infrastructure "
        "millions of records breached across power grid hospital government"
    )
    art = compute_article_score_v2(title, summary)
    assert art.track_b <= 80.0


def test_title_keyword_boost_cap_20():
    # Title saturated with TIER1/TIER2 keywords; total Track B should still respect 80 cap.
    title = "zero-day ransomware backdoor rce supply chain"
    art = compute_article_score_v2(title, "")
    assert art.track_b <= 80.0


def test_keyword_score_can_saturate_at_25():
    from pipeline.scoring_v2 import _extract_keyword_score_normalized
    text = "zero-day ransomware backdoor rce supply chain critical infrastructure"
    score = _extract_keyword_score_normalized(text.lower())
    assert score > 20.0, f"keyword score should saturate near 25, got {score}"


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


from datetime import datetime, timedelta, timezone
from pipeline.scoring_v2 import compute_global_score_v2, GlobalScore


def _article(score, trigger=None, age_hours=0, title="t", aid="x"):
    return {
        "id": aid,
        "title": title,
        "defcon_score": float(score),
        "defcon_trigger": trigger,
        "published_at": datetime.now(timezone.utc) - timedelta(hours=age_hours),
    }


def test_global_v2_empty_window_zero():
    g = compute_global_score_v2(articles_in_window=[], new_count=0, baseline=None)
    assert g.score == 0.0
    assert g.trigger is None
    assert g.weighted_max == 0.0


def test_global_v2_picks_highest_weighted():
    arts = [
        _article(90, trigger="active_exploitation", age_hours=0, aid="a"),
        _article(50, trigger=None, age_hours=0, aid="b"),
    ]
    g = compute_global_score_v2(arts, new_count=5, baseline=5.0)
    assert g.weighted_max == pytest.approx(90.0)
    assert g.trigger == "active_exploitation"
    assert g.trigger_article_id == "a"


def test_global_v2_age_decays_weight():
    # 90-pt article, 12h old, weight = 0.5 → contribution = 45
    # 50-pt article, 0h old, weight = 1.0 → contribution = 50
    arts = [
        _article(90, trigger="active_exploitation", age_hours=12, aid="old"),
        _article(50, trigger=None, age_hours=0, aid="fresh"),
    ]
    g = compute_global_score_v2(arts, new_count=5, baseline=5.0)
    assert g.trigger_article_id == "fresh"
    assert g.weighted_max == pytest.approx(50.0)


def test_global_v2_volume_bonus_baseline_zero():
    arts = [_article(40, age_hours=0)]
    g = compute_global_score_v2(arts, new_count=10, baseline=5.0)
    # ratio 2.0, bonus = clamp((2.0-1.0)*10, 0, 10) = 10
    assert g.volume_bonus == pytest.approx(10.0)


def test_global_v2_volume_bonus_capped():
    arts = [_article(40, age_hours=0)]
    g = compute_global_score_v2(arts, new_count=100, baseline=5.0)
    assert g.volume_bonus == pytest.approx(10.0)


def test_global_v2_volume_bonus_below_baseline_zero():
    arts = [_article(40, age_hours=0)]
    g = compute_global_score_v2(arts, new_count=2, baseline=5.0)
    assert g.volume_bonus == 0.0


def test_global_v2_cold_start_no_volume_bonus():
    arts = [_article(40, age_hours=0)]
    g = compute_global_score_v2(arts, new_count=10, baseline=None)
    assert g.volume_bonus == 0.0


def test_global_v2_total_clamped_100():
    arts = [_article(95, trigger="active_exploitation", age_hours=0)]
    g = compute_global_score_v2(arts, new_count=100, baseline=5.0)
    assert g.score == 100.0  # 95 + 10 capped


# --- Scope amplifier impact signals ---

def test_impact_billions_of_devices():
    raw = _extract_impact_raw_v2("flaw affects billions of devices worldwide")
    assert raw >= 5


def test_impact_every_version():
    raw = _extract_impact_raw_v2("present in every version of the kernel")
    assert raw >= 4


def test_impact_any_linux_system():
    raw = _extract_impact_raw_v2("works on any linux system released since 2015")
    assert raw >= 4


def test_impact_amplifier_neutral_text_zero():
    raw = _extract_impact_raw_v2("microsoft released routine patches this month")
    assert raw == 0


def test_cve_inference_zero_day_with_scope():
    text = "new linux zero-day affects all major linux distributions"
    assert _extract_cvss_v2(text) == 8.0


def test_cve_inference_rce_unauthenticated():
    text = "unauthenticated remote code execution flaw disclosed"
    assert _extract_cvss_v2(text) == 8.0


def test_cve_inference_root_with_scope():
    text = "kernel flaw grants root on any linux system"
    assert _extract_cvss_v2(text) == 7.5


def test_cve_inference_no_scope_no_inference():
    text = "zero-day vulnerability discovered in obscure cms plugin"
    assert _extract_cvss_v2(text) == 0.0


def test_cve_inference_explicit_cvss_still_wins():
    text = "zero-day in all major linux distros, cvss 9.5 confirmed"
    assert _extract_cvss_v2(text) == 9.5


# --- Calibration target tests ---


def test_calibration_clickfix_macos_stealer_campaign():
    title = "Fake macOS Troubleshooting Sites Used to Steal iCloud Data in ClickFix Scam"
    summary = (
        "Microsoft researchers warn of a new ClickFix campaign targeting macOS "
        "with fake guides on Medium and Craft to deploy AMOS and SHub Stealer "
        "via Terminal commands."
    )
    art = compute_article_score_v2(title, summary)
    assert art.trigger == "malware_campaign", f"expected malware_campaign, got {art.trigger}"
    assert 45 <= art.score <= 75, f"expected 45-75, got {art.score}"


def test_calibration_dirty_frag_linux_zero_day():
    title = "New Linux 'Dirty Frag' zero-day gives root on all major distros"
    summary = (
        "A new Linux zero-day vulnerability, named Dirty Frag, allows local "
        "attackers to gain root privileges on most major Linux distributions "
        "with a single command."
    )
    art = compute_article_score_v2(title, summary)
    assert art.trigger == "critical_scope_vuln", f"expected critical_scope_vuln, got {art.trigger}"
    assert 70 <= art.score <= 88, f"expected 70-88, got {art.score}"


def test_calibration_routine_patch_news_stays_low():
    title = "Microsoft releases August security patches"
    summary = (
        "Microsoft has released its monthly security update covering several "
        "Windows components. Administrators are advised to review and deploy."
    )
    art = compute_article_score_v2(title, summary)
    assert art.trigger is None, f"unexpected trigger {art.trigger}"
    assert art.score < 30, f"expected <30, got {art.score}"


def test_calibration_active_exploitation_still_high():
    title = "CVE-2026-1234 actively exploited in attacks against Fortinet appliances"
    summary = (
        "Researchers report active exploitation of a critical authentication "
        "bypass with cvss 9.8, used by attackers in the wild."
    )
    art = compute_article_score_v2(title, summary)
    assert art.trigger == "active_exploitation"
    assert art.score >= 80, f"expected >=80, got {art.score}"
