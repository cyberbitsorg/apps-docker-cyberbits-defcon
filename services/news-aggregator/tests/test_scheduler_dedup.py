from scheduler import _within_batch_duplicate


def test_batch_cve_no_trigger_to_trigger_allows():
    """Existing batch article had no trigger; new article has one → escalation allowed."""
    seen = [("NGINX CVE-2026-42945 patch released", "", None)]
    result = _within_batch_duplicate(
        "NGINX CVE-2026-42945 exploited in the wild",
        "",
        seen,
    )
    assert result is False


def test_batch_cve_both_triggered_blocks():
    """Both articles share a CVE and both have triggers → second is blocked."""
    seen = [("NGINX CVE-2026-42945 exploited in the wild", "", "active_exploitation")]
    result = _within_batch_duplicate(
        "Experts warn of NGINX CVE-2026-42945 active exploitation",
        "",
        seen,
    )
    assert result is True


def test_batch_cve_existing_triggered_new_untriggered_blocks():
    """Existing article has trigger; new article has no trigger → blocked."""
    seen = [("NGINX CVE-2026-42945 exploited in the wild", "", "active_exploitation")]
    result = _within_batch_duplicate(
        "NGINX CVE-2026-42945 patch released",
        "",
        seen,
    )
    assert result is True


def test_batch_no_cve_overlap_unaffected():
    """Articles with no shared CVEs are not affected by this logic."""
    seen = [("Apache log4j CVE-2021-44228 patch released", "", None)]
    result = _within_batch_duplicate(
        "NGINX CVE-2026-42945 exploited in the wild",
        "",
        seen,
    )
    assert result is False
