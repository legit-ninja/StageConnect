from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.offering import ActivityType, EquipmentProvided


class OfferingCreateRequest(BaseModel):
    act_id: UUID
    activity_type: ActivityType
    price: Decimal = Field(ge=0, decimal_places=2)
    availability: str | None = Field(default=None, max_length=2000)
    promoter_only_allowed: bool = False
    active: bool = True
    display_location: str | None = Field(default=None, max_length=256)
    min_booker_experience: int | None = Field(default=None, ge=1, le=5)
    max_venue_capacity: int | None = Field(default=None, ge=50, le=500)
    sound_system_required: bool = True
    equipment_provided: EquipmentProvided = EquipmentProvided.EITHER


class OfferingUpdateRequest(BaseModel):
    activity_type: ActivityType | None = None
    price: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    availability: str | None = Field(default=None, max_length=2000)
    promoter_only_allowed: bool | None = None
    active: bool | None = None
    min_booker_experience: int | None = Field(default=None, ge=1, le=5)
    max_venue_capacity: int | None = Field(default=None, ge=50, le=500)
    sound_system_required: bool | None = None
    equipment_provided: EquipmentProvided | None = None


class OfferingSummary(BaseModel):
    id: UUID
    act_id: UUID
    act_name: str
    genre_id: UUID
    activity_type: ActivityType
    price: Decimal
    availability: str | None
    promoter_only_allowed: bool
    slug: str
    display_location: str
    public_lat: float
    public_lng: float
    photo_urls: list[str]
    genres: list[str] = Field(default_factory=list)
    min_booker_experience: int | None = None
    max_venue_capacity: int | None = None
    sound_system_required: bool = True
    equipment_provided: EquipmentProvided = EquipmentProvided.EITHER
    created_at: datetime


class OfferingDetail(OfferingSummary):
    act_owner_id: UUID
    description: str | None
    act_type: str | None
    active: bool


class OfferingResponse(BaseModel):
    id: UUID
    act_id: UUID
    act_owner_id: UUID
    activity_type: ActivityType
    price: Decimal
    availability: str | None
    promoter_only_allowed: bool
    active: bool
    slug: str
    display_location: str
    public_lat: float
    public_lng: float
    min_booker_experience: int | None = None
    max_venue_capacity: int | None = None
    sound_system_required: bool = True
    equipment_provided: EquipmentProvided = EquipmentProvided.EITHER
    created_at: datetime

    model_config = {"from_attributes": True}
