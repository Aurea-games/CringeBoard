from pydantic import BaseModel, Field, field_validator, model_validator

from .validators import normalize_email


class LoginRequest(BaseModel):
    email: str = Field(
        ...,
        description="User email address used to authenticate.",
        examples=["user@example.com"],
    )
    password: str = Field(
        ...,
        description="Account password.",
        examples=["change-me-123"],
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return normalize_email(value)


class RegisterRequest(BaseModel):
    email: str = Field(
        ...,
        description="User email that will serve as the login identifier.",
        examples=["new.user@example.org"],
    )
    password: str = Field(
        ...,
        min_length=8,
        description="Desired account password (minimum 8 characters).",
        examples=["Str0ngPass!"],
    )
    confirm_password: str = Field(
        ...,
        min_length=8,
        description="Confirmation of the password to avoid typos.",
        examples=["Str0ngPass!"],
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return normalize_email(value)

    @model_validator(mode="after")
    def validate_passwords(self) -> "RegisterRequest":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        if len(self.password) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        return self


class TokenResponse(BaseModel):
    access_token: str = Field(
        ...,
        description="Short-lived access token granting API access.",
        examples=["eyJhbGciOiJIUzI1NiIsInR5..."],
    )
    refresh_token: str = Field(
        ...,
        description="Longer-lived token used to refresh the session.",
        examples=["dGhpc19pc19hX3NhbXBsZV9yZWZyZXNoX3Rva2Vu"],
    )
    token_type: str = Field(
        default="bearer",
        description="Token type according to RFC 6750.",
        examples=["bearer"],
    )


class RefreshRequest(BaseModel):
    refresh_token: str = Field(
        ...,
        min_length=1,
        description="Refresh token obtained during authentication.",
        examples=["dGhpc19pc19hX3NhbXBsZV9yZWZyZXNoX3Rva2Vu"],
    )


__all__ = ["LoginRequest", "RegisterRequest", "TokenResponse", "RefreshRequest"]
