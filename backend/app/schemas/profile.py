"""Profile update and account settings schemas."""

from typing import Optional
from pydantic import BaseModel, Field, field_validator


class ProfileUpdateRequest(BaseModel):
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    country: Optional[str] = Field(None, max_length=100)
    preferred_currency: Optional[str] = Field(None, min_length=3, max_length=10)

    @field_validator("preferred_currency")
    @classmethod
    def clean_currency(cls, v: Optional[str]) -> Optional[str]:
        if v:
            clean = v.strip().upper()
            allowed = {"USD", "EUR", "GBP", "CAD", "AUD", "INR", "JPY", "CHF", "SGD"}
            if clean not in allowed:
                return "USD"
            return clean
        return v


class DeleteAccountRequest(BaseModel):
    password: str = Field(..., min_length=1, max_length=128, description="Current password for re-authentication")
    confirmation_text: str = Field(..., description="Must explicitly match 'DELETE'")

    @field_validator("confirmation_text")
    @classmethod
    def validate_confirmation(cls, v: str) -> str:
        if v.strip() != "DELETE":
            raise ValueError("Confirmation text must be 'DELETE'")
        return v
