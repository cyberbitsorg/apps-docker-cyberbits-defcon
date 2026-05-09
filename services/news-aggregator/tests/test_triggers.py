from pipeline.triggers import detect_trigger, TRIGGER_BASE, _has_scope_amplifier, _is_newsletter_title


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


def test_kev_catalog_fires_kev_addition():
    assert detect_trigger("microsoft adds cve to kev catalog").trigger == "kev_addition"


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
    # "known exploited" + cisa + adds → kev_addition wins over confirmed_breach
    text = "cisa adds known exploited bug; vendor confirms breach affecting millions"
    assert detect_trigger(text).trigger == "kev_addition"


def test_no_false_positive_apt_substring():
    # "capture" contains "apt" but should not fire
    assert detect_trigger("capture chapter captain government targets") is None


def test_returns_matched_text_for_logging():
    result = detect_trigger("actively exploited rce")
    assert "actively exploited" in result.matched_text.lower()


def test_trigger_base_scores():
    assert TRIGGER_BASE["active_exploitation"] == 80
    assert TRIGGER_BASE["kev_addition"] == 75
    assert TRIGGER_BASE["critical_scope_vuln"] == 70
    assert TRIGGER_BASE["confirmed_breach"] == 70
    assert TRIGGER_BASE["apt_campaign"] == 65
    assert TRIGGER_BASE["malware_campaign"] == 60


def test_scope_amplifier_all_major_distros():
    assert _has_scope_amplifier("vulnerability affects all major linux distributions")


def test_scope_amplifier_billions_of_devices():
    assert _has_scope_amplifier("flaw affects billions of devices worldwide")


def test_scope_amplifier_every_version():
    assert _has_scope_amplifier("present in every version of the kernel")


def test_scope_amplifier_any_linux():
    assert _has_scope_amplifier("works on any linux system")


def test_scope_amplifier_negative_routine():
    assert not _has_scope_amplifier("affects some windows servers running specific software")


def test_scope_amplifier_negative_single_product():
    assert not _has_scope_amplifier("vulnerability in cisco asa firewall")


def test_critical_scope_vuln_zero_day_all_distros():
    text = "new linux 'dirty frag' zero-day gives root on all major linux distros"
    match = detect_trigger(text)
    assert match is not None
    assert match.trigger == "critical_scope_vuln"


def test_critical_scope_vuln_rce_billions_of_devices():
    text = "remote code execution flaw affects billions of devices"
    match = detect_trigger(text)
    assert match is not None
    assert match.trigger == "critical_scope_vuln"


def test_critical_scope_vuln_priv_esc_every_version():
    text = "privilege escalation vulnerability present in every version of the kernel"
    match = detect_trigger(text)
    assert match is not None
    assert match.trigger == "critical_scope_vuln"


def test_critical_scope_vuln_no_scope_no_trigger():
    text = "zero-day vulnerability in fortinet vpn appliance disclosed"
    match = detect_trigger(text)
    assert match is None or match.trigger != "critical_scope_vuln"


def test_critical_scope_vuln_scope_alone_no_trigger():
    text = "all major linux distributions release scheduled monthly updates"
    match = detect_trigger(text)
    assert match is None or match.trigger != "critical_scope_vuln"


def test_malware_campaign_stealer_targeting():
    text = "new infostealer campaign targeting macos via fake support sites"
    match = detect_trigger(text)
    assert match is not None
    assert match.trigger == "malware_campaign"


def test_malware_campaign_known_stealer_deploys():
    text = "fake macos guides deploy amos and shub stealer via terminal commands"
    match = detect_trigger(text)
    assert match is not None
    assert match.trigger == "malware_campaign"


def test_malware_campaign_loader_distributes():
    text = "new loader distributes secondary payloads to enterprise endpoints"
    match = detect_trigger(text)
    assert match is not None
    assert match.trigger == "malware_campaign"


def test_malware_campaign_rat_with_word_boundary():
    text = "remote access trojan (rat) drops on victim machines"
    match = detect_trigger(text)
    assert match is not None
    assert match.trigger == "malware_campaign"


def test_malware_campaign_stealer_alone_no_trigger():
    text = "researchers analyzed redline stealer source code"
    match = detect_trigger(text)
    assert match is None or match.trigger != "malware_campaign"


def test_malware_campaign_campaign_word_alone_no_trigger():
    text = "marketing campaign targets gen z consumers"
    match = detect_trigger(text)
    assert match is None or match.trigger != "malware_campaign"


def test_malware_campaign_no_false_positive_rat_substring():
    text = "rate limiting accelerates degrade and corporate strategy"
    match = detect_trigger(text)
    assert match is None or match.trigger != "malware_campaign"


def test_active_exploitation_exploits_cve():
    text = "mirai botnet exploits cve-2025-29635 to target legacy d-link routers"
    match = detect_trigger(text)
    assert match is not None and match.trigger == "active_exploitation"


def test_active_exploitation_exploited_as_zero_day():
    text = "nasty cpanel vulnerability probably exploited as a 0-day"
    match = detect_trigger(text)
    assert match is not None and match.trigger == "active_exploitation"


def test_active_exploitation_weaponized():
    text = "researchers report weaponized exploit chain affecting fortinet"
    match = detect_trigger(text)
    assert match is not None and match.trigger == "active_exploitation"


def test_active_exploitation_exploiting():
    text = "threat actors exploiting unpatched ivanti appliances"
    match = detect_trigger(text)
    assert match is not None and match.trigger == "active_exploitation"


def test_no_false_positive_exploits_marketing():
    # "exploits opportunity" must NOT fire active_exploitation
    text = "company exploits market opportunity in cybersecurity sector"
    match = detect_trigger(text)
    assert match is None or match.trigger != "active_exploitation"


def test_is_newsletter_title_round():
    assert _is_newsletter_title("Security Affairs Newsletter Round 574")


def test_is_newsletter_title_weekly_roundup():
    assert _is_newsletter_title("Weekly roundup of cybersecurity news")


def test_is_newsletter_title_negative():
    assert not _is_newsletter_title("CISA Adds Three Linux Flaws to KEV Catalog")
