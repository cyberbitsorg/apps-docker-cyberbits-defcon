_VOLUME_KEY = "defcon:volume_history"
_WINDOW_SIZE = 168
_COLD_START_MIN = 3
_POISON_MULTIPLIER = 3.0


async def record_volume(redis, new_count: int) -> None:
    """
    Push new_count to the rolling window and trim to the last 168 entries.
    Skips entries >3x the current baseline (cold-start dumps that would poison the average).
    """
    baseline = await get_volume_baseline(redis)
    if baseline is not None and baseline > 0 and new_count > _POISON_MULTIPLIER * baseline:
        return
    await redis.rpush(_VOLUME_KEY, new_count)
    await redis.ltrim(_VOLUME_KEY, -_WINDOW_SIZE, -1)


async def get_volume_baseline(redis) -> float | None:
    entries = await redis.lrange(_VOLUME_KEY, 0, -1)
    if len(entries) < _COLD_START_MIN:
        return None
    values = [float(e.decode() if isinstance(e, bytes) else e) for e in entries]
    return sum(values) / len(values)
