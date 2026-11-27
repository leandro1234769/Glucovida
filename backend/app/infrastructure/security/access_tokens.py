from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID, uuid4

import jwt
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey

from app.application.auth.login import LoginSession


ACCESS_TOKEN_SECONDS = 900


@dataclass(frozen=True)
class AccessClaims:
    user_id: UUID
    session_id: UUID
    auth_version: int


class AccessTokenSigner:
    def __init__(self, pem: bytes, issuer: str, audience: str):
        key = load_pem_private_key(pem, password=None)
        if not isinstance(key, RSAPrivateKey) or key.key_size < 2048:
            raise ValueError("Access tokens require an RSA key of at least 2048 bits")
        self._key = key
        self._public_key = key.public_key()
        self._issuer = issuer
        self._audience = audience

    def issue(self, session: LoginSession) -> str:
        return jwt.encode({
            "iss": self._issuer, "aud": self._audience,
            "sub": str(session.user_id), "sid": str(session.session_id),
            "jti": str(uuid4()), "av": session.auth_version,
            "iat": session.created_at,
            "exp": min(session.expires_at, session.created_at + timedelta(seconds=ACCESS_TOKEN_SECONDS)),
        }, self._key, algorithm="RS256")

    def decode(self, token: str) -> AccessClaims:
        data = jwt.decode(
            token, self._public_key, algorithms=["RS256"],
            issuer=self._issuer, audience=self._audience,
            options={"require": ["iss", "aud", "sub", "sid", "jti", "av", "iat", "exp"]},
        )
        try:
            if type(data["av"]) is not int or data["av"] < 1:
                raise ValueError
            UUID(data["jti"])
            return AccessClaims(UUID(data["sub"]), UUID(data["sid"]), data["av"])
        except (AttributeError, ValueError, TypeError):
            raise jwt.InvalidTokenError("Invalid access claims") from None
