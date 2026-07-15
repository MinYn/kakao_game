"""Redis 기반 고트래픽 런타임 유틸리티.

10k RPS 대응에서 API/봇 프로세스가 공통으로 쓸 수 있는 rate limit,
idempotency, leaderboard 기능을 제공한다. Kafka는 이벤트 내구성/비동기 처리,
Redis는 초저지연 상태 조회/제어에 집중하도록 역할을 분리한다.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Protocol

from config import Config


class RedisLike(Protocol):
    """테스트 대역과 redis-py 클라이언트가 만족해야 하는 최소 인터페이스."""

    def incr(self, name: str) -> int: ...

    def expire(self, name: str, time: int) -> bool: ...

    def set(self, name: str, value: str, ex: int | None = None, nx: bool = False) -> bool | None: ...

    def zadd(self, name: str, mapping: dict[str, float]) -> int: ...

    def zrevrange(self, name: str, start: int, end: int, withscores: bool = False) -> list: ...

    def zrevrank(self, name: str, value: str) -> int | None: ...

    def close(self) -> None: ...


@dataclass(frozen=True)
class RateLimitResult:
    """Rate limit 평가 결과."""

    allowed: bool
    current_count: int
    limit: int
    retry_after_seconds: int


@dataclass(frozen=True)
class LeaderboardEntry:
    """Redis Sorted Set 기반 리더보드 항목."""

    user_id: str
    score: int
    rank: int


class RedisRuntime:
    """Redis를 사용하는 고빈도 요청 보조 기능 모음."""

    def __init__(self, client: RedisLike | None = None) -> None:
        if client is not None:
            self.client = client
            return

        from redis import Redis

        self.client = Redis.from_url(
            Config.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=Config.REDIS_SOCKET_TIMEOUT_SECONDS,
            socket_timeout=Config.REDIS_SOCKET_TIMEOUT_SECONDS,
            health_check_interval=30,
        )

    def check_rate_limit(
        self,
        *,
        subject: str,
        action: str,
        limit: int = Config.REDIS_RATE_LIMIT_PER_MINUTE,
        window_seconds: int = 60,
    ) -> RateLimitResult:
        """고정 윈도우 방식 rate limit을 검사한다."""

        bucket = int(time.time() // window_seconds)
        key = f"rate:{action}:{subject}:{bucket}"
        current_count = int(self.client.incr(key))
        if current_count == 1:
            self.client.expire(key, window_seconds)

        return RateLimitResult(
            allowed=current_count <= limit,
            current_count=current_count,
            limit=limit,
            retry_after_seconds=window_seconds if current_count > limit else 0,
        )

    def reserve_idempotency_key(
        self,
        *,
        namespace: str,
        key: str,
        ttl_seconds: int = Config.REDIS_IDEMPOTENCY_TTL_SECONDS,
    ) -> bool:
        """중복 요청 방지를 위해 idempotency key를 선점한다."""

        redis_key = f"idem:{namespace}:{key}"
        return bool(self.client.set(redis_key, "1", ex=ttl_seconds, nx=True))

    def update_leaderboard(self, *, board: str, user_id: str, score: int) -> None:
        """리더보드 점수를 반영한다."""

        self.client.zadd(f"leaderboard:{board}", {user_id: score})

    def get_leaderboard(self, *, board: str, limit: int = 100) -> list[LeaderboardEntry]:
        """상위 랭킹을 조회한다."""

        rows = self.client.zrevrange(f"leaderboard:{board}", 0, limit - 1, withscores=True)
        entries: list[LeaderboardEntry] = []
        for index, row in enumerate(rows, start=1):
            user_id, score = row
            entries.append(LeaderboardEntry(user_id=str(user_id), score=int(score), rank=index))
        return entries

    def get_rank(self, *, board: str, user_id: str) -> int | None:
        """사용자의 1-based 랭킹을 반환한다."""

        rank = self.client.zrevrank(f"leaderboard:{board}", user_id)
        return None if rank is None else int(rank) + 1

    def close(self) -> None:
        """Redis 연결을 종료한다."""

        self.client.close()
