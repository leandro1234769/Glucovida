import hmac
from math import ceil
from dataclasses import dataclass
from ipaddress import ip_address
from uuid import UUID, uuid4

from redis.asyncio import Redis
from redis.exceptions import WatchError


@dataclass(frozen=True)
class RateLimit:
    requests: int
    window_seconds: int

    def __post_init__(self) -> None:
        if self.requests <= 0 or self.window_seconds <= 0:
            raise ValueError("Rate limits and their windows must be positive")


class RegistrationRateLimited(Exception):
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__("Registration rate limit reached")


class RegistrationRateLimiter:
    def __init__(
        self, redis: Redis, *, key_secret: bytes, per_ip: RateLimit, per_email: RateLimit, scope: str = "register",
    ):
        if len(key_secret) < 32:
            raise ValueError("Rate-limit key secret must contain at least 32 bytes")
        self._scope = scope
        self._redis = redis
        self._key_secret = key_secret
        self._per_ip = per_ip
        self._per_email = per_email

    @staticmethod
    def _normalize_address(client_ip: str) -> str:
        address = ip_address(client_ip)
        if address.version == 6 and address.ipv4_mapped is not None:
            address = address.ipv4_mapped
        return str(address)

    async def require_confirmation(self, client_ip: str) -> None:
        address = self._normalize_address(client_ip)
        await self._require_limits({f"rl:{{confirm}}:ip:{address}": self._per_ip})

    async def require_refresh_ip(self, client_ip: str) -> None:
        address = self._normalize_address(client_ip)
        await self._require_limits({f"rl:{{refresh}}:ip:{address}": self._per_ip})

    async def require_refresh_session(self, session_id: UUID) -> None:
        await self._require_limits({f"rl:{{refresh}}:session:{session_id}": RateLimit(5, 60)})

    async def require(self, client_ip: str, normalized_email: str) -> None:
        address = self._normalize_address(client_ip)
        email_key = hmac.digest(
            self._key_secret, normalized_email.encode("utf-8"), "sha256"
        ).hex()
        await self._require_limits({
            f"rl:{{{self._scope}}}:ip:{address}": self._per_ip,
            f"rl:{{{self._scope}}}:email:{email_key}": self._per_email,
        })

    async def _require_limits(self, limits: dict[str, RateLimit]) -> None:
        # WATCH ties the admission decision to the same counters written by EXEC.
        for _ in range(8):
            async with self._redis.pipeline() as pipeline:
                try:
                    await pipeline.watch(*limits)
                    seconds, microseconds = await pipeline.time()
                    now = seconds * 1000 + microseconds // 1000
                    retry_ms = 0
                    for key, limit in limits.items():
                        window_ms = limit.window_seconds * 1000
                        boundary = await pipeline.zrevrangebyscore(
                            key, "+inf", f"({now - window_ms}",
                            start=limit.requests - 1, num=1, withscores=True,
                        )
                        if boundary:
                            retry_ms = max(retry_ms, boundary[0][1] + window_ms - now)

                    pipeline.multi()
                    if retry_ms:
                        pipeline.ping()
                    else:
                        request_id = uuid4().hex
                        for key, limit in limits.items():
                            window_ms = limit.window_seconds * 1000
                            pipeline.zremrangebyscore(key, "-inf", now - window_ms)
                            pipeline.zadd(key, {request_id: now})
                            pipeline.pexpire(key, window_ms)
                    await pipeline.execute()
                    if retry_ms:
                        raise RegistrationRateLimited(ceil(retry_ms / 1000))
                    return
                except WatchError:
                    continue

        raise RegistrationRateLimited(1)
