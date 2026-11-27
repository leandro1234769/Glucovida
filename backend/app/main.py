from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.api.csrf import create_csrf_router
from app.api.login import create_login_router
from app.api.registration import create_registration_router
from app.database.session import create_database_engine
from app.infrastructure.redis.registration_limits import RateLimit, RegistrationRateLimiter
from app.infrastructure.security.access_tokens import AccessTokenSigner
from app.registration_settings import RegistrationSettings


def create_app(settings: RegistrationSettings | None = None) -> FastAPI:
    settings = settings or RegistrationSettings()
    registration_enabled = settings.registration_enabled()
    login_enabled = settings.environment in {"development", "test"} and settings.jwt_private_key_file is not None
    csrf = settings.csrf_protection()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if not (registration_enabled or login_enabled):
            yield
            return

        if settings.database_url is None:
            raise ValueError("DATABASE_URL is required for authentication")
        database = create_database_engine(settings.database_url.get_secret_value())
        try:
            async with Redis.from_url(
                settings.redis_url.get_secret_value(), socket_timeout=5, socket_connect_timeout=5
            ) as redis:
                app.state.database_sessions = async_sessionmaker(database, expire_on_commit=False)
                if registration_enabled:
                    app.state.registration_workflow = settings.registration_workflow(redis)
                if login_enabled:
                    app.state.csrf = csrf
                    app.state.access_token_signer = AccessTokenSigner(
                        settings.jwt_private_key_file.read_bytes(), settings.jwt_issuer, settings.jwt_audience
                    )
                    app.state.login_limits = RegistrationRateLimiter(
                        redis, key_secret=settings.rate_limit_key.get_secret_value().encode("utf-8"),
                        per_ip=RateLimit(30, 300), per_email=RateLimit(30, 300), scope="login",
                    )
                yield
        finally:
            await database.dispose()

    app = FastAPI(title="GlucoVida", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=sorted(settings.allowed_origins),
        allow_credentials=True,
        allow_methods=["GET", "POST"] if registration_enabled or login_enabled else ["GET"],
        allow_headers=["Authorization", "Content-Type", "X-CSRF-Token"],
        expose_headers=["X-CSRF-Token", "Retry-After"],
    )
    app.include_router(create_csrf_router(csrf))
    if registration_enabled:
        app.include_router(create_registration_router())
    if login_enabled:
        app.include_router(create_login_router())
    return app
