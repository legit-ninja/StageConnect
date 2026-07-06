from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models.user import User, VerificationStatus


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    is_booker: bool = True
    is_act_owner: bool = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UpdateProfileRequest(BaseModel):
    is_act_manager: bool | None = None
    is_booking_coordinator: bool | None = None
    booker_experience_level: int | None = Field(default=None, ge=1, le=5)


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    is_booker: bool
    is_act_owner: bool
    is_act_manager: bool
    is_booking_coordinator: bool
    manager_verified: bool
    booker_experience_level: int | None
    is_admin: bool
    verification_status: VerificationStatus
    is_minor: bool
    created_at: datetime
    avatar_url: str | None = None

    model_config = {"from_attributes": True}
