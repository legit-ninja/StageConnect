from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.oauth_account import OAuthProvider
from app.models.user import VerificationStatus


class OAuthAccountSummary(BaseModel):
    provider: OAuthProvider
    provider_email: str | None
    provider_email_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminGuardianSummary(BaseModel):
    id: UUID
    email: str
    verification_status: VerificationStatus


class AdminUserSummary(BaseModel):
    id: UUID
    email: str
    is_booker: bool
    is_act_owner: bool
    is_act_manager: bool
    is_booking_coordinator: bool
    manager_verified: bool
    is_admin: bool
    verification_status: VerificationStatus
    is_minor: bool
    booker_experience_level: int | None = None
    oauth_providers: list[OAuthProvider]
    created_at: datetime


class AdminUserDetail(AdminUserSummary):
    phone: str | None
    guardian_user_id: UUID | None
    guardian: AdminGuardianSummary | None = None
    oauth_accounts: list[OAuthAccountSummary]
    act_count: int = 0
    offering_count: int = 0
    active_offering_count: int = 0


class AdminUserListResponse(BaseModel):
    items: list[AdminUserSummary]
    total: int
    limit: int
    offset: int


class AdminStatsResponse(BaseModel):
    total_users: int
    admin_users: int
    verified_users: int
    unverified_users: int
    pending_users: int
    rejected_users: int
    booker_users: int
    act_owner_users: int
    manager_users: int
    verified_manager_users: int
    oauth_users: int
    signups_last_7d: int
    total_acts: int
    total_offerings: int
    active_offerings: int


class AdminOfferingSummary(BaseModel):
    id: UUID
    act_name: str
    act_owner_email: str
    activity_type: str
    price: Decimal
    availability: str | None
    active: bool
    created_at: datetime


class AdminOfferingListResponse(BaseModel):
    items: list[AdminOfferingSummary]
    total: int


class UpdateOfferingActiveRequest(BaseModel):
    active: bool


class UpdateVerificationRequest(BaseModel):
    verification_status: VerificationStatus
    note: str | None = Field(default=None, max_length=500)


class UpdateUserRolesRequest(BaseModel):
    is_booker: bool
    is_act_owner: bool


class UpdateTrainerVerificationRequest(BaseModel):
    manager_verified: bool
    note: str | None = Field(default=None, max_length=500)


class AdminAuditLogEntry(BaseModel):
    id: UUID
    actor_id: UUID
    actor_email: str
    action: str
    target_user_id: UUID | None
    target_user_email: str | None
    metadata: dict
    created_at: datetime


class AdminAuditLogListResponse(BaseModel):
    items: list[AdminAuditLogEntry]
    total: int
    limit: int
    offset: int


class AdminPlatformFlagSummary(BaseModel):
    id: UUID
    user_id: UUID
    user_email: str
    flag_type: str
    details: dict | None
    created_at: datetime
    resolved_at: datetime | None


class AdminPlatformFlagListResponse(BaseModel):
    items: list[AdminPlatformFlagSummary]
    total: int
