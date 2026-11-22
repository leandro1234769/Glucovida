import asyncio
import smtplib
from unittest.mock import MagicMock

import pytest
from fakeredis import FakeServer
from fakeredis.aioredis import FakeRedis
from pydantic import SecretStr

from app.infrastructure.email.verification import SmtpVerificationSender, VerificationDeliveryError
from app.infrastructure.redis.registration_limits import (
    RateLimit,
    RegistrationRateLimited,
    RegistrationRateLimiter,
)
from app.infrastructure.security import csrf


ORIGIN = "https://app.example.com"


def test_csrf_requires_matching_signed_fresh_token_and_allowed_origin(monkeypatch):
    monkeypatch.setattr(csrf, "time", lambda: 1000)
    protection = csrf.CsrfProtection(b"s" * 32, frozenset({ORIGIN}))
    token = protection.issue()
    protection.require(ORIGIN, token, token)

    altered = token[:-1] + ("0" if token[-1] != "0" else "1")
    for origin, cookie, header in [
        (None, token, token),
        ("https://other.example.com", token, token),
        (ORIGIN, None, token),
        (ORIGIN, token, None),
        (ORIGIN, token, altered),
        (ORIGIN, altered, altered),
    ]:
        with pytest.raises(csrf.CsrfRejected):
            protection.require(origin, cookie, header)

    monkeypatch.setattr(csrf, "time", lambda: 1000 + csrf.CSRF_MAX_AGE)
    with pytest.raises(csrf.CsrfRejected):
        protection.require(ORIGIN, token, token)


def test_smtp_sends_verification_token_in_fragment_and_maps_delivery_errors(monkeypatch):
    smtp = MagicMock()
    client = smtp.return_value.__enter__.return_value
    monkeypatch.setattr(smtplib, "SMTP_SSL", smtp)
    sender = SmtpVerificationSender(
        host="smtp.example.com", port=465, sender="noreply@example.com",
        verification_page="https://app.example.com/verify",
        username="smtp-user", password=SecretStr("smtp-secret"),
    )
    asyncio.run(sender.send("ana@example.com", SecretStr("verification-secret")))
    assert smtp.call_args.args == ("smtp.example.com", 465)
    client.login.assert_called_once_with("smtp-user", "smtp-secret")
    message = client.send_message.call_args.args[0]
    assert message["To"] == "ana@example.com"
    assert "https://app.example.com/verify#token=verification-secret" in message.get_content()

    client.send_message.side_effect = smtplib.SMTPException("transport error")
    with pytest.raises(VerificationDeliveryError):
        asyncio.run(sender.send("ana@example.com", SecretStr("verification-secret")))


def test_rate_limits_are_shared_and_atomic():
    async def run():
        server = FakeServer()
        async with FakeRedis(server=server) as first, FakeRedis(server=server) as second:
            options = {
                "key_secret": b"s" * 32,
                "per_ip": RateLimit(2, 60),
                "per_email": RateLimit(1, 60),
            }
            one = RegistrationRateLimiter(first, **options)
            two = RegistrationRateLimiter(second, **options)
            attempts = await asyncio.gather(
                one.require("192.0.2.1", "ana@example.com"),
                two.require("192.0.2.2", "ana@example.com"),
                return_exceptions=True,
            )
            assert attempts.count(None) == 1
            rejected = next(result for result in attempts if result is not None)
            assert isinstance(rejected, RegistrationRateLimited)
            assert 1 <= rejected.retry_after <= 60

            await one.require("192.0.2.3", "b@example.com")
            await two.require("::ffff:192.0.2.3", "c@example.com")
            with pytest.raises(RegistrationRateLimited):
                await one.require("192.0.2.3", "d@example.com")

            keys = await first.keys("*")
            assert all(b"@example.com" not in key for key in keys)
            for key in keys:
                await first.zadd(key, {member: 0 for member in await first.zrange(key, 0, -1)})
            await two.require("192.0.2.3", "ana@example.com")

    asyncio.run(run())


def test_smtp_starttls_precedes_authentication(monkeypatch):
    smtp = MagicMock()
    client = smtp.return_value.__enter__.return_value
    monkeypatch.setattr(smtplib, "SMTP", smtp)
    sender = SmtpVerificationSender(
        host="smtp.example.com", port=587, sender="noreply@example.com",
        verification_page="https://app.example.com/verify",
        username="smtp-user", password=SecretStr("smtp-secret"), starttls=True,
    )
    asyncio.run(sender.send("ana@example.com", SecretStr("verification-secret")))

    assert [call[0] for call in client.method_calls] == ["starttls", "login", "send_message"]
