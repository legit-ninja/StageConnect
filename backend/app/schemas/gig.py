from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class CreateGigRequest(BaseModel):
    offering_id: UUID
    availability_slot_id: UUID | None = None
    note: str | None = Field(default=None, max_length=2000)


class UpdateGigStatusRequest(BaseModel):
    status: str = Field(
        pattern="^(approved|declined|cancelled|completed|counter_offer)$"
    )
    counter_offer_price: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    counter_offer_scheduled_at: datetime | None = None
    counter_offer_note: str | None = Field(default=None, max_length=2000)


class GigResponse(BaseModel):
    id: UUID
    offering_id: UUID
    act_name: str
    booker_id: UUID
    rider_email: str
    rider_verification_status: str
    act_owner_id: UUID
    act_owner_email: str
    payment_type: str
    status: str
    scheduled_at: datetime | None
    availability_slot_id: UUID | None = None
    note: str | None
    requested_at: datetime
    offering_price: Decimal
    activity_type: str
    thread_id: UUID | None = None
    booker_experience_warning: str | None = None
    counter_offer_price: Decimal | None = None
    counter_offer_scheduled_at: datetime | None = None
    counter_offer_note: str | None = None
    confirmed_snapshot: dict | None = None

    model_config = {"from_attributes": True}


class GigListResponse(BaseModel):
    items: list[GigResponse]
    total: int
