from events.redis_runtime import RedisRuntime


class FakeRedis:
    def __init__(self):
        self.values = {}
        self.sorted_sets = {}
        self.expirations = {}

    def incr(self, name: str) -> int:
        self.values[name] = int(self.values.get(name, 0)) + 1
        return self.values[name]

    def expire(self, name: str, time: int) -> bool:
        self.expirations[name] = time
        return True

    def set(self, name: str, value: str, ex: int | None = None, nx: bool = False) -> bool | None:
        if nx and name in self.values:
            return None
        self.values[name] = value
        if ex is not None:
            self.expirations[name] = ex
        return True

    def zadd(self, name: str, mapping: dict[str, float]) -> int:
        zset = self.sorted_sets.setdefault(name, {})
        created = 0
        for member, score in mapping.items():
            if member not in zset:
                created += 1
            zset[member] = score
        return created

    def zrevrange(self, name: str, start: int, end: int, withscores: bool = False) -> list:
        rows = sorted(self.sorted_sets.get(name, {}).items(), key=lambda item: item[1], reverse=True)
        selected = rows[start : end + 1]
        return selected if withscores else [member for member, _ in selected]

    def zrevrank(self, name: str, value: str) -> int | None:
        members = self.zrevrange(name, 0, 10_000, withscores=False)
        if value not in members:
            return None
        return members.index(value)

    def close(self) -> None:
        return None


def test_rate_limit_blocks_after_limit():
    runtime = RedisRuntime(client=FakeRedis())

    first = runtime.check_rate_limit(subject="u1", action="score", limit=2)
    second = runtime.check_rate_limit(subject="u1", action="score", limit=2)
    third = runtime.check_rate_limit(subject="u1", action="score", limit=2)

    assert first.allowed is True
    assert second.allowed is True
    assert third.allowed is False
    assert third.current_count == 3


def test_idempotency_key_can_be_reserved_once():
    runtime = RedisRuntime(client=FakeRedis())

    assert runtime.reserve_idempotency_key(namespace="score", key="evt-1") is True
    assert runtime.reserve_idempotency_key(namespace="score", key="evt-1") is False


def test_leaderboard_returns_ranked_entries():
    runtime = RedisRuntime(client=FakeRedis())

    runtime.update_leaderboard(board="global", user_id="u1", score=100)
    runtime.update_leaderboard(board="global", user_id="u2", score=300)
    runtime.update_leaderboard(board="global", user_id="u3", score=200)

    entries = runtime.get_leaderboard(board="global", limit=2)

    assert [entry.user_id for entry in entries] == ["u2", "u3"]
    assert [entry.rank for entry in entries] == [1, 2]
    assert runtime.get_rank(board="global", user_id="u1") == 3
