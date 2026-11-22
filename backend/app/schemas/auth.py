from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr, StrictBool, StringConstraints
from pydantic import field_validator


DocumentVersion = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9._-]+$")
]


class ConsentVersions(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    terms_version: DocumentVersion
    privacy_version: DocumentVersion
    health_data_version: DocumentVersion


class RegistrationConsentInput(ConsentVersions):
    terms_accepted: Literal[True]
    privacy_acknowledged: Literal[True]
    health_data_authorized: StrictBool

    @field_validator("terms_accepted", "privacy_acknowledged", mode="before")
    @classmethod
    def require_explicit_acceptance(cls, value: object) -> object:
        if value is not True:
            raise ValueError("The decision must be explicitly affirmative")
        return value


class VerificationResendInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    email: EmailStr

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


class RegistrationInput(VerificationResendInput):
    names: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]
    surnames: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
    password: SecretStr
    consent: RegistrationConsentInput

    @field_validator("names", "surnames")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if "\x00" in value:
            raise ValueError("Names must not contain null characters")
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


class LoginInput(VerificationResendInput):
    password: SecretStr

    @field_validator("password")
    @classmethod
    def validate_password_size(cls, value: SecretStr) -> SecretStr:
        password = value.get_secret_value()
        if not password or len(password.encode("utf-8")) > 72:
            raise ValueError("Invalid password length")
        return value
