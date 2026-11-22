from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.api.csrf import create_csrf_router
from app.api.registration import create_registration_router
from app.database.session import create_database_engine
from app.registration_settings import RegistrationSettings


def create_app(settings: RegistrationSettings | None = None) -> FastAPI:
    settings = settings or RegistrationSettings()
    registration_enabled = settings.registration_enabled()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if not registration_enabled:
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
                app.state.registration_workflow = settings.registration_workflow(redis)
                yield
        finally:
            await database.dispose()

    app = FastAPI(title="GlucoVida", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=sorted(settings.allowed_origins),
        allow_credentials=True,
        allow_methods=["GET", "POST"] if registration_enabled else ["GET"],
        allow_headers=["Content-Type", "X-CSRF-Token"],
    )
    app.include_router(create_csrf_router(settings.csrf_protection()))
    if registration_enabled:
        app.include_router(create_registration_router())
    return app
