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
    assert TRIGGER_BASE["active_exploitation"] == 70
    assert TRIGGER_BASE["kev_addition"] == 70
    assert TRIGGER_BASE["critical_scope_vuln"] == 65
    assert TRIGGER_BASE["confirmed_breach"] == 65
    assert TRIGGER_BASE["apt_campaign"] == 60
    assert TRIGGER_BASE["malware_campaign"] == 55


def test_exploiting_human_trust_is_not_active_exploitation():
    # Regression: "exploiting human trust" / "exploiting confusion" should NOT trigger.
    text = "ai hallucinations create security risks by exploiting human trust in models"
    assert detect_trigger(text) is None


def test_exploiting_a_vuln_still_triggers():
    assert detect_trigger("attackers exploiting a critical RCE flaw").trigger == "active_exploitation"
    assert detect_trigger("threat actor exploiting cve-2026-12345").trigger == "active_exploitation"


def test_pwn2own_does_not_trigger_active_exploitation():
    # Pwn2Own is a contest — "exploited" descriptions are research, not in-the-wild.
    assert detect_trigger("windows 11 and microsoft edge hacked at pwn2own berlin 2026 — researchers exploited a zero-day") is None


def test_ctf_does_not_trigger():
    assert detect_trigger("team exploited zero-day during defcon ctf finals") is None


def test_actively_exploited_still_fires_outside_contest():
    # Sanity: regular wild exploitation phrasing still works.
    assert detect_trigger("fortinet fortigate flaw actively exploited in the wild").trigger == "active_exploitation"


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


def test_breach_theft_of_records():
    text = "shinyhunters claimed theft of 9m+ records from medtronic"
    match = detect_trigger(text)
    assert match is not None and match.trigger == "confirmed_breach"


def test_breach_stealing_auth_tokens():
    text = "global campaign stealing auth tokens from 35k users"
    match = detect_trigger(text)
    assert match is not None and match.trigger == "confirmed_breach"


def test_breach_scale_with_plus_sign():
    # The 9M+ pattern with trailing + must be detected as a numeric scale
    from pipeline.triggers import _BREACH_SCALE_NUMERIC
    assert _BREACH_SCALE_NUMERIC.search("dump of 9M+ records confirmed")


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


def test_apt_threat_actor_with_breach_verb_no_sector():
    # ShinyHunters + theft verb, no critical sector — must trigger something
    # (apt_campaign or confirmed_breach takes precedence based on PRECEDENCE).
    text = "shinyhunters group breach campaign hits multiple companies this week"
    match = detect_trigger(text)
    assert match is not None
    assert match.trigger in ("apt_campaign", "confirmed_breach")


def test_apt_no_actor_no_sector_no_verb_no_trigger():
    text = "weekly cybersecurity industry briefing summary"
    match = detect_trigger(text)
    assert match is None


def test_is_newsletter_title_round():
    assert _is_newsletter_title("Security Affairs Newsletter Round 574")


def test_is_newsletter_title_weekly_roundup():
    assert _is_newsletter_title("Weekly roundup of cybersecurity news")


def test_is_newsletter_title_negative():
    assert not _is_newsletter_title("CISA Adds Three Linux Flaws to KEV Catalog")


def test_active_exploitation_negated_never_exploited():
    text = "critical crowdstrike logscale bug, the flaw was never exploited in the wild"
    match = detect_trigger(text)
    assert match is None or match.trigger != "active_exploitation"


def test_active_exploitation_negated_no_exploitation():
    text = "critical flaw disclosed, but no exploitation was observed"
    match = detect_trigger(text)
    assert match is None or match.trigger != "active_exploitation"


def test_active_exploitation_negated_unsuccessful():
    text = "cve-2023-33538 under attack for a year, but exploitation still unsuccessful"
    match = detect_trigger(text)
    assert match is None or match.trigger != "active_exploitation"


def test_active_exploitation_positive_unchanged():
    # Sanity: actually-exploited articles still trigger
    text = "ivanti vulnerability actively exploited in attacks against enterprises"
    match = detect_trigger(text)
    assert match is not None and match.trigger == "active_exploitation"


def test_active_exploitation_negation_does_not_apply_to_distant_match():
    # If "no" appears 100 chars before, it should NOT suppress
    text = ("no problems were reported with last quarter's deployment process. "
            "however a separate critical flaw is now actively exploited in the wild")
    match = detect_trigger(text)
    assert match is not None and match.trigger == "active_exploitation"


def test_malware_campaign_infects_verb():
    text = "fake claude ai site infects users with new beagle malware"
    match = detect_trigger(text)
    assert match is not None and match.trigger == "malware_campaign"


def test_breach_scale_comma_separated_people():
    text = "zara data breach exposed personal information of 197,000 people"
    match = detect_trigger(text)
    assert match is not None and match.trigger == "confirmed_breach"


def test_breach_scale_comma_separated_schools():
    text = "instructure data breach may have impacted 9,000 schools across the us"
    match = detect_trigger(text)
    assert match is not None and match.trigger == "confirmed_breach"


def test_breach_scale_comma_no_breach_verb_no_trigger():
    text = "annual report shows growth at 197,000 customers across regions"
    match = detect_trigger(text)
    assert match is None or match.trigger != "confirmed_breach"


def test_critical_sector_rail_triggers_path():
    # Taiwan High-Speed Rail Emergency Braking Hack — railway is critical infra
    text = "taiwan high-speed rail emergency braking hack stops trains across country"
    # apt or breach trigger may fire depending on verb. Just confirm SOMETHING fires
    # via the critical sector path.
    from pipeline.triggers import _CRITICAL_SECTOR_RE
    assert _CRITICAL_SECTOR_RE.search(text) is not None


def test_critical_sector_schools_in_breach():
    text = "data breach may have impacted thousands of schools nationwide"
    from pipeline.triggers import _CRITICAL_SECTOR_RE
    assert _CRITICAL_SECTOR_RE.search(text) is not None


def test_active_exploitation_cashing_in():
    text = "attackers are cashing in on fresh copyfail linux flaw exploited via stack overflow"
    match = detect_trigger(text)
    assert match is not None and match.trigger == "active_exploitation"


def test_active_exploitation_wave_of_attacks():
    text = "wave of attacks targeting unpatched fortinet vpn appliances reported"
    match = detect_trigger(text)
    assert match is not None and match.trigger == "active_exploitation"


def test_active_exploitation_in_active_use():
    text = "rce flaw is in active use by attackers across multiple regions"
    match = detect_trigger(text)
    assert match is not None and match.trigger == "active_exploitation"


def test_no_false_positive_cashing_in_business():
    text = "tech firm cashing in on the booming AI sector this quarter"
    match = detect_trigger(text)
    assert match is None or match.trigger != "active_exploitation"


def test_breach_exposed_personal_information():
    text = "zara breach exposed personal information of 197,000 people"
    match = detect_trigger(text)
    assert match is not None and match.trigger == "confirmed_breach"


def test_breach_exposed_alone_not_a_breach():
    # `exposed AI services` should NOT fire breach
    text = "we scanned 1 million exposed ai services in our research project"
    match = detect_trigger(text)
    assert match is None or match.trigger != "confirmed_breach"


def test_breach_scale_numeric_repos():
    # 5k repos breached — numeric k-style scale
    from pipeline.triggers import _BREACH_SCALE_NUMERIC
    assert _BREACH_SCALE_NUMERIC.search("breach of 5k repos confirmed")


def test_breach_scale_numeric_packages():
    from pipeline.triggers import _BREACH_SCALE_NUMERIC
    assert _BREACH_SCALE_NUMERIC.search("200k packages affected in supply chain attack")


def test_breach_scale_comma_repos():
    # 3,800 repos — comma-separated style (the GitHub article)
    from pipeline.triggers import _BREACH_SCALE_COMMA
    assert _BREACH_SCALE_COMMA.search("breach of 3,800 repos confirmed")


def test_breach_scale_comma_packages():
    from pipeline.triggers import _BREACH_SCALE_COMMA
    assert _BREACH_SCALE_COMMA.search("supply chain attack affecting 15,000 packages")


def test_no_false_positive_repos_without_breach_verb():
    # "shares 3,800 repos" has no breach verb — must not fire confirmed_breach
    text = "developer shares 3,800 repos on github under open source license"
    match = detect_trigger(text)
    assert match is None or match.trigger != "confirmed_breach"


def test_no_false_positive_packages_without_breach_verb():
    text = "npm publishes 15,000 packages per day as ecosystem grows"
    match = detect_trigger(text)
    assert match is None or match.trigger != "confirmed_breach"


def test_confirmed_breach_github_repos():
    # The article that triggered this fix: GitHub breach of 3,800 repos
    text = "github confirms breach of 3,800 repos via malicious vscode extension"
    match = detect_trigger(text)
    assert match is not None
    assert match.trigger == "confirmed_breach"


def test_confirmed_breach_npm_packages_comma():
    text = "npm registry data breach exposes source code of 15,000 packages"
    match = detect_trigger(text)
    assert match is not None
    assert match.trigger == "confirmed_breach"
