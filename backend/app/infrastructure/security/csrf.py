import hmac
import re
from secrets import token_urlsafe
from time import time


CSRF_COOKIE = "__Host-gv_csrf"
CSRF_MAX_AGE = 86400
_TOKEN_FORMAT = re.compile(r"[0-9]{1,12}\.[A-Za-z0-9_-]{43}\.[0-9a-f]{64}")


class CsrfRejected(Exception):
    """The request did not pass its origin and CSRF checks."""


class CsrfProtection:
    def __init__(self, signing_key: bytes, allowed_origins: frozenset[str]):
        if len(signing_key) < 32:
            raise ValueError("CSRF signing key must contain at least 32 bytes")
        if not allowed_origins or "null" in allowed_origins or "*" in allowed_origins:
            raise ValueError("Configure explicit allowed origins")
        self._signing_key = signing_key
        self._allowed_origins = allowed_origins

    def issue(self) -> str:
        payload = f"{int(time())}.{token_urlsafe(32)}"
        return f"{payload}.{self._signature(payload)}"

    def require_origin(self, origin: str | None) -> None:
        if origin not in self._allowed_origins:
            raise CsrfRejected("Invalid origin or CSRF token")

    def require(self, origin: str | None, cookie: str | None, header: str | None) -> None:
        self.require_origin(origin)
        if cookie is None or header is None:
            raise CsrfRejected("Invalid origin or CSRF token")
        if (
            not _TOKEN_FORMAT.fullmatch(cookie)
            or len(header) != len(cookie)
            or not header.isascii()
            or not hmac.compare_digest(cookie, header)
        ):
            raise CsrfRejected("Invalid origin or CSRF token")

        payload, signature = cookie.rsplit(".", 1)
        if not hmac.compare_digest(self._signature(payload), signature):
            raise CsrfRejected("Invalid origin or CSRF token")
        issued_at = int(payload.split(".", 1)[0])
        if not 0 <= int(time()) - issued_at < CSRF_MAX_AGE:
            raise CsrfRejected("Invalid origin or CSRF token")

    def _signature(self, payload: str) -> str:
        return hmac.digest(self._signing_key, payload.encode("ascii"), "sha256").hex()
