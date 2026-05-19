import pytest
from pipeline.deduplicator import is_duplicate, CVES_KEY


class _FakeRedis:
    """Minimal in-memory Redis stand-in covering the ops used by is_duplicate()."""

    def __init__(self):
        self._sets: dict[str, set] = {}
        self._strings: dict[str, str] = {}
        self._lists: dict[str, list] = {}

    async def sismember(self, key, value):
        return value in self._sets.get(key, set())

    async def sadd(self, key, value):
        self._sets.setdefault(key, set()).add(value)

    async def expire(self, key, ttl):
        pass

    async def exists(self, key):
        return 1 if key in self._strings else 0

    async def get(self, key):
        val = self._strings.get(key)
        return val.encode() if val is not None else None

    async def set(self, key, value, ex=None):
        self._strings[key] = str(value)

    async def lpush(self, key, value):
        self._lists.setdefault(key, []).insert(0, value)

    async def ltrim(self, key, start, end):
        lst = self._lists.get(key, [])
        self._lists[key] = lst[start : end + 1] if end >= 0 else lst[start:]

    async def lrange(self, key, start, end):
        lst = self._lists.get(key, [])
        return lst[start : end + 1] if end >= 0 else lst[start:]


@pytest.fixture
def redis():
    return _FakeRedis()


@pytest.mark.asyncio
async def test_cve_seen_no_trigger_blocks(redis):
    """CVE stored as 'none', new article has no trigger → blocked."""
    await redis.set(f"{CVES_KEY}:CVE-2026-42945", "none")
    result = await is_duplicate("NGINX CVE-2026-42945 patch released", redis)
    assert result is True


@pytest.mark.asyncio
async def test_cve_seen_with_trigger_allows_escalation(redis):
    """CVE stored as 'none', new article has active_exploitation trigger → allowed."""
    await redis.set(f"{CVES_KEY}:CVE-2026-42945", "none")
    result = await is_duplicate("NGINX CVE-2026-42945 exploited in the wild", redis)
    assert result is False


@pytest.mark.asyncio
async def test_cve_already_escalated_blocks(redis):
    """CVE stored as a trigger name → all further articles blocked even with trigger."""
    await redis.set(f"{CVES_KEY}:CVE-2026-42945", "active_exploitation")
    result = await is_duplicate("NGINX CVE-2026-42945 exploited in the wild", redis)
    assert result is True


@pytest.mark.asyncio
async def test_cve_legacy_value_blocks(redis):
    """Legacy '1' stored value is treated as already-escalated, new article blocked."""
    await redis.set(f"{CVES_KEY}:CVE-2026-42945", "1")
    result = await is_duplicate("NGINX CVE-2026-42945 exploited in the wild", redis)
    assert result is True


@pytest.mark.asyncio
async def test_first_article_stores_none_when_no_trigger(redis):
    """First article with CVE but no trigger stores 'none'."""
    await is_duplicate("NGINX CVE-2026-42945 patch released", redis)
    stored = await redis.get(f"{CVES_KEY}:CVE-2026-42945")
    assert stored == b"none"


@pytest.mark.asyncio
async def test_first_article_stores_trigger_name(redis):
    """First article with CVE and a trigger stores the trigger name."""
    await is_duplicate("NGINX CVE-2026-42945 exploited in the wild", redis)
    stored = await redis.get(f"{CVES_KEY}:CVE-2026-42945")
    assert stored == b"active_exploitation"


@pytest.mark.asyncio
async def test_escalation_updates_cve_key(redis):
    """After an escalation article passes, CVE key is updated to the trigger name."""
    await redis.set(f"{CVES_KEY}:CVE-2026-42945", "none")
    await is_duplicate("NGINX CVE-2026-42945 exploited in the wild", redis)
    stored = await redis.get(f"{CVES_KEY}:CVE-2026-42945")
    assert stored == b"active_exploitation"
