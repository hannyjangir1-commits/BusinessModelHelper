"""Authentication request and response schemas."""

import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=30, description="Alphanumeric username with underscores or hyphens")
    email: str = Field(..., min_length=5, max_length=255, description="Valid email address")
    password: str = Field(..., min_length=8, max_length=128, description="Strong password")
    confirm_password: str = Field(..., min_length=8, max_length=128)
    terms_accepted: bool = Field(..., description="Must explicitly accept Terms and Conditions")
    privacy_acknowledged: bool = Field(..., description="Must explicitly acknowledge Privacy Policy")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        clean = v.strip()
        if not re.match(r"^[a-zA-Z0-9_-]{3,30}$", clean):
            raise ValueError("Username must be 3-30 characters and contain only letters, numbers, underscores, and hyphens.")
        return clean.lower()

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        clean = v.strip().lower()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", clean):
            raise ValueError("Please provide a valid email address.")
        return clean

    @model_validator(mode="after")
    def validate_passwords_and_legal(self) -> "UserRegisterRequest":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        if not self.terms_accepted:
            raise ValueError("You must accept the Terms and Conditions to register.")
        if not self.privacy_acknowledged:
            raise ValueError("You must acknowledge the Privacy Policy to register.")
        return self


class UserLoginRequest(BaseModel):
    username_or_email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=1, max_length=128)

    @field_validator("username_or_email")
    @classmethod
    def clean_identifier(cls, v: str) -> str:
        return v.strip().lower()


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_new_password: str = Field(..., min_length=8, max_length=128)

    @model_validator(mode="after")
    def validate_passwords(self) -> "ChangePasswordRequest":
        if self.new_password != self.confirm_new_password:
            raise ValueError("New passwords do not match.")
        if self.current_password == self.new_password:
            raise ValueError("New password must be different from current password.")
        return self


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    display_name: str
    bio: Optional[str] = None
    country: Optional[str] = None
    preferred_currency: str = "USD"
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class AuthResponse(BaseModel):
    user: UserResponse
    csrf_token: str
    message: str = "Authenticated successfully"
