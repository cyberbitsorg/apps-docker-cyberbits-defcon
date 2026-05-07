import pytest
from unittest.mock import AsyncMock
from cache.volume import record_volume, get_volume_baseline

VOLUME_KEY = "defcon:volume_history"


@pytest.fixture
def redis():
    r = AsyncMock()
    r.lrange = AsyncMock(return_value=[])
    return r


@pytest.mark.asyncio
async def test_record_volume_pushes_count(redis):
    await record_volume(redis, 7)
    redis.rpush.assert_called_once_with(VOLUME_KEY, 7)


@pytest.mark.asyncio
async def test_record_volume_trims_to_168_entries(redis):
    await record_volume(redis, 7)
    redis.ltrim.assert_called_once_with(VOLUME_KEY, -168, -1)


@pytest.mark.asyncio
async def test_get_volume_baseline_cold_start_returns_none(redis):
    redis.lrange.return_value = [b"5", b"7"]  # only 2 entries — below threshold
    result = await get_volume_baseline(redis)
    assert result is None


@pytest.mark.asyncio
async def test_get_volume_baseline_exactly_three_entries(redis):
    redis.lrange.return_value = [b"9", b"12", b"9"]
    result = await get_volume_baseline(redis)
    assert result == pytest.approx(10.0)


@pytest.mark.asyncio
async def test_get_volume_baseline_averages_correctly(redis):
    redis.lrange.return_value = [b"5", b"15", b"10", b"10", b"10"]
    result = await get_volume_baseline(redis)
    assert result == pytest.approx(10.0)


@pytest.mark.asyncio
async def test_get_volume_baseline_queries_full_list(redis):
    redis.lrange.return_value = [b"10", b"10", b"10"]
    await get_volume_baseline(redis)
    redis.lrange.assert_called_once_with(VOLUME_KEY, 0, -1)


class _FakeRedis:
    """Minimal in-memory stand-in for the Redis methods we use."""
    def __init__(self):
        self._lists = {}
    async def rpush(self, key, val):
        self._lists.setdefault(key, []).append(str(val).encode())
    async def ltrim(self, key, start, end):
        lst = self._lists.get(key, [])
        # Mirror Redis ltrim semantics for negative indices
        if start < 0: start = max(0, len(lst) + start)
        if end < 0:  end  = len(lst) + end
        self._lists[key] = lst[start:end + 1]
    async def lrange(self, key, start, end):
        lst = self._lists.get(key, [])
        if end == -1: end = len(lst) - 1
        return lst[start:end + 1]


@pytest.mark.asyncio
async def test_record_volume_skips_poison_entry():
    """A new_count >3x the current baseline should NOT be recorded (cold-start dump)."""
    r = _FakeRedis()
    # Seed baseline at ~5
    for v in [4, 5, 6, 5]:
        await record_volume(r, v)
    baseline_before = await get_volume_baseline(r)
    assert baseline_before == pytest.approx(5.0)

    # Try to record a poison value (5x baseline)
    await record_volume(r, 25)

    baseline_after = await get_volume_baseline(r)
    # Should be unchanged (entry skipped)
    assert baseline_after == pytest.approx(5.0)


@pytest.mark.asyncio
async def test_record_volume_records_during_cold_start():
    """When baseline is None (cold start), every value is recorded."""
    r = _FakeRedis()
    # Below cold-start threshold (3 entries)
    await record_volume(r, 100)
    await record_volume(r, 100)
    entries = await r.lrange("defcon:volume_history", 0, -1)
    assert len(entries) == 2
