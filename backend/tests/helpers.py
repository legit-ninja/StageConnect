from decimal import Decimal
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.models.act import Act
from app.models.offering import ActivityType, Offering, EquipmentProvided
from app.models.offering_availability_slot import OfferingAvailabilitySlot, SlotStatus
from app.models.user import User
from app.config import settings
from app.services.public_location import default_display_location, jitter_coordinates
from app.services.slug import generate_offering_slug


def seed_test_offering(
    db: Session,
    *,
    jazz_genre,
    owner: User,
    act_name: str = "TestBand",
    activity_type: ActivityType = ActivityType.WEDDING,
    price: Decimal = Decimal("50.00"),
    promoter_only_allowed: bool = False,
    active: bool = True,
    lat: float = 36.2,
    lng: float = -81.6,
    address: str = "Boone, NC",
    min_booker_experience: int | None = None,
    max_venue_capacity: int | None = None,
    sound_system_required: bool = True,
    equipment_provided: EquipmentProvided = EquipmentProvided.EITHER,
) -> Offering:
    act = Act(
        act_owner_id=owner.id,
        genre_id=jazz_genre.id,
        name=act_name,
        lat=lat,
        lng=lng,
        address=address,
        photo_urls=[],
        genres=["jazz"],
    )
    db.add(act)
    db.flush()
    public_lat, public_lng = jitter_coordinates(
        act.id, lat, lng, settings.service_area_default_secret
    )
    offering = Offering(
        act_id=act.id,
        act_owner_id=owner.id,
        activity_type=activity_type,
        price=price,
        promoter_only_allowed=promoter_only_allowed,
        active=active,
        slug=generate_offering_slug(act_name),
        display_location=default_display_location(address),
        public_lat=public_lat,
        public_lng=public_lng,
        min_booker_experience=min_booker_experience,
        max_venue_capacity=max_venue_capacity,
        sound_system_required=sound_system_required,
        equipment_provided=equipment_provided,
    )
    db.add(offering)
    db.commit()
    db.refresh(offering)
    return offering


def seed_test_slot(
    db: Session,
    *,
    offering: Offering,
    days_ahead: int = 3,
    hours: int = 10,
    duration_hours: int = 2,
    status: SlotStatus = SlotStatus.OPEN,
) -> OfferingAvailabilitySlot:
    start_at = datetime.now(UTC) + timedelta(days=days_ahead, hours=hours)
    end_at = start_at + timedelta(hours=duration_hours)
    slot = OfferingAvailabilitySlot(
        offering_id=offering.id,
        start_at=start_at,
        end_at=end_at,
        status=status,
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)
    return slot
