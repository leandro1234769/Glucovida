from ipaddress import ip_address
from typing import TypeVar

from fastapi import HTTPException, Request
from pydantic import BaseModel, ValidationError

from app.application.auth.registration_workflow import RegistrationContext
from app.infrastructure.security.csrf import CSRF_COOKIE


_MAX_BODY_SIZE = 8192
Payload = TypeVar("Payload", bound=BaseModel)


async def read_payload(request: Request, model: type[Payload]) -> Payload:
    media_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if media_type != "application/json":
        raise HTTPException(415, "Expected application/json")

    body = bytearray()
    async for chunk in request.stream():
        if len(chunk) > _MAX_BODY_SIZE - len(body):
            raise HTTPException(413, "Request body is too large")
        body.extend(chunk)

    try:
        return model.model_validate_json(bytes(body))
    except ValidationError:
        raise HTTPException(400, "Invalid request body") from None


def request_context(request: Request) -> RegistrationContext:
    try:
        address = str(ip_address(request.client.host)) if request.client else None
    except ValueError:
        address = None
    if address is None:
        raise HTTPException(400, "Invalid client address")
    return RegistrationContext(
        address, request.headers.get("origin"), request.cookies.get(CSRF_COOKIE),
        request.headers.get("x-csrf-token"),
    )
