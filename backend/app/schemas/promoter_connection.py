from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class CreatePromoterConnectionRequest(BaseModel):
    invitee_email: EmailStr


class PromoterConnectionResponse(BaseModel):
    id: UUID
    act_owner_id: UUID
    booker_id: UUID | None
    invitee_email: EmailStr
    status: str
    invited_at: datetime
    accepted_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PromoterConnectionListResponse(BaseModel):
    items: list[PromoterConnectionResponse]


class UpdatePromoterConnectionStatusRequest(BaseModel):
    status: str = Field(pattern="^(accepted|declined|revoked)$")
