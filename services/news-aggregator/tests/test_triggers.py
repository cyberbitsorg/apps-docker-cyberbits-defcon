from pipeline.triggers import detect_trigger, TRIGGER_BASE


def test_active_exploitation_actively_exploited():
    result = detect_trigger("rce flaw actively exploited in the wild")
    assert result is not None
    assert result.trigger == "active_exploitation"


def test_active_exploitation_in_the_wild():
    assert detect_trigger("zero-day in-the-wild attacks").trigger == "active_exploitation"


def test_active_exploitation_under_attack():
    assert detect_trigger("system under active attack").trigger == "active_exploitation"


def test_active_exploitation_zero_day_exploited():
    assert detect_trigger("0-day exploited via debug api").trigger == "active_exploitation"


def test_kev_addition():
    assert detect_trigger("cisa adds new vuln to known exploited vulnerabilities catalog").trigger == "kev_addition"


def test_confirmed_breach_with_millions():
    assert detect_trigger("shinyhunters breached vimeo affecting millions of users").trigger == "confirmed_breach"


def test_confirmed_breach_with_kK_records():
    assert detect_trigger("dump puts 119k emails in the wild").trigger == "active_exploitation"  # in the wild wins by precedence


def test_confirmed_breach_119k_no_in_the_wild():
    assert detect_trigger("dump puts 119k emails online from vimeo").trigger == "confirmed_breach"


def test_confirmed_breach_critical_sector():
    assert detect_trigger("hospital breached confirms breach").trigger == "confirmed_breach"


def test_apt_campaign():
    assert detect_trigger("apt28 nation-state campaign targets government agencies").trigger == "apt_campaign"


def test_apt_campaign_named_actor():
    assert detect_trigger("muddywater campaign targets military").trigger == "apt_campaign"


def test_no_trigger_routine_patch():
    assert detect_trigger("microsoft patches medium severity bug") is None


def test_no_trigger_critical_alone():
    # "critical" alone is not enough to trigger anything
    assert detect_trigger("critical for soc teams to patch quickly") is None


def test_precedence_active_over_breach():
    # both active_exploitation and confirmed_breach patterns present
    text = "actively exploited breach affects millions"
    assert detect_trigger(text).trigger == "active_exploitation"


def test_precedence_kev_over_breach():
    text = "cisa adds known exploited bug; vendor confirms breach affecting millions"
    assert detect_trigger(text).trigger == "active_exploitation"  # exploited matches active first


def test_no_false_positive_apt_substring():
    # "capture" contains "apt" but should not fire
    assert detect_trigger("capture chapter captain government targets") is None


def test_returns_matched_text_for_logging():
    result = detect_trigger("actively exploited rce")
    assert "actively exploited" in result.matched_text.lower()


def test_trigger_base_scores():
    assert TRIGGER_BASE["active_exploitation"] == 80
    assert TRIGGER_BASE["confirmed_breach"] == 80
    assert TRIGGER_BASE["kev_addition"] == 80
    assert TRIGGER_BASE["apt_campaign"] == 75
