from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr, StringConstraints
from pydantic import field_validator


class RegistrationInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    names: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]
    surnames: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
    email: EmailStr
    password: SecretStr

    @field_validator("names", "surnames")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if "\x00" in value:
            raise ValueError("Names must not contain null characters")
        return value

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @field_validator("email")
    @classmethod
    def validate_email_length(cls, value: str) -> str:
        value = value.lower()
        if len(value) > 254:
            raise ValueError("Email must be at most 254 characters")
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: SecretStr) -> SecretStr:
        password = value.get_secret_value()
        if len(password) < 8 or not password.strip():
            raise ValueError("Password must contain at least 8 characters and not be blank")
        if len(password.encode("utf-8")) > 72:
            raise ValueError("Password must be at most 72 UTF-8 bytes")
        return value


class RegistrationResult(BaseModel):
    """Internal result for the future verification email sender."""

    user_id: UUID
    verification_token: SecretStr = Field(exclude=True, repr=False)
