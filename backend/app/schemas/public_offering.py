from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.offering import EquipmentProvided


def equipment_provided_label(value: EquipmentProvided | str) -> str:
    if isinstance(value, str):
        value = EquipmentProvided(value)
    labels = {
        EquipmentProvided.PROVIDED: "Full backline provided",
        EquipmentProvided.BRING_OWN: "Venue provides equipment",
        EquipmentProvided.EITHER: "Negotiable",
    }
    return labels[value]


class PublicOffering(BaseModel):
    """Allowlist-only public act/offering response. No private location or contact fields."""

    act_name: str
    genre: str
    act_type: str | None
    years_active: int | None
    photo_urls: list[str]
    activity_type: str
    price: Decimal | None
    display_location: str
    public_lat: float
    public_lng: float
    act_owner_first_name: str
    act_owner_last_initial: str
    act_owner_verified: bool
    act_owner_manager_verified: bool = False
    act_owner_member_since: str
    review_count: int
    review_average: float | None
    slug: str
    active: bool
    genres: list[str] = Field(default_factory=list)
    min_booker_experience: int | None = None
    min_booker_experience_label: str | None = None
    max_venue_capacity: int | None = None
    sound_system_required: bool = True
    equipment_provided: str = EquipmentProvided.EITHER.value
    equipment_provided_label: str = equipment_provided_label(EquipmentProvided.EITHER)


class PublicInvitePreview(BaseModel):
    act_owner_first_name: str
    act_owner_verified: bool
    act_names: list[str]
    token_valid: bool
    expired: bool = False
    revoked: bool = False
