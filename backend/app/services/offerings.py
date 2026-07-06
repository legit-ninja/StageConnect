import math
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.act import Act
from app.models.offering import ActivityType, Offering
from app.models.genre import Genre, GenreCatalog
from app.schemas.offering import OfferingDetail, OfferingSummary


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius_km = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lng2 - lng1)
    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return radius_km * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def offering_to_summary(offering: Offering) -> OfferingSummary:
    act = offering.act
    return OfferingSummary(
        id=offering.id,
        act_id=offering.act_id,
        act_name=act.name,
        genre_id=act.genre_id,
        activity_type=offering.activity_type,
        price=offering.price,
        availability=offering.availability,
        promoter_only_allowed=offering.promoter_only_allowed,
        slug=offering.slug,
        display_location=offering.display_location,
        public_lat=offering.public_lat,
        public_lng=offering.public_lng,
        photo_urls=list(act.photo_urls or []),
        genres=list(act.genres or []),
        min_booker_experience=offering.min_booker_experience,
        max_venue_capacity=offering.max_venue_capacity,
        sound_system_required=offering.sound_system_required,
        equipment_provided=offering.equipment_provided,
        created_at=offering.created_at,
    )


def offering_to_detail(offering: Offering) -> OfferingDetail:
    summary = offering_to_summary(offering)
    act = offering.act
    return OfferingDetail(
        **summary.model_dump(),
        act_owner_id=offering.act_owner_id,
        description=act.description,
        act_type=act.act_type,
        active=offering.active,
    )


def search_offerings(
    db: Session,
    *,
    activity_type: ActivityType | None,
    genre_id: UUID | None,
    min_price: Decimal | None,
    max_price: Decimal | None,
    lat: float,
    lng: float,
    radius_km: float,
    genre: Genre | None = None,
    active_only: bool = True,
    act_owner_id: UUID | None = None,
) -> list[Offering]:
    stmt = select(Offering).options(
        selectinload(Offering.act).selectinload(Act.genre_catalog)
    )
    if active_only:
        stmt = stmt.where(Offering.active.is_(True))
    if act_owner_id is not None:
        stmt = stmt.where(Offering.act_owner_id == act_owner_id)
    if activity_type is not None:
        stmt = stmt.where(Offering.activity_type == activity_type)
    if min_price is not None:
        stmt = stmt.where(Offering.price >= min_price)
    if max_price is not None:
        stmt = stmt.where(Offering.price <= max_price)
    if genre_id is not None:
        stmt = stmt.join(Act, Offering.act_id == Act.id).where(Act.genre_id == genre_id)

    offerings = list(db.scalars(stmt.order_by(Offering.created_at.desc())).all())

    filtered: list[Offering] = []
    for offering in offerings:
        distance = haversine_km(lat, lng, offering.public_lat, offering.public_lng)
        if distance > radius_km:
            continue
        if genre is not None:
            styles = list(offering.act.genres or [])
            if genre.value not in styles:
                continue
        filtered.append(offering)
    return filtered


def get_offering_detail(db: Session, offering_id: UUID) -> Offering | None:
    return db.scalar(
        select(Offering)
        .options(selectinload(Offering.act).selectinload(Act.genre_catalog))
        .where(Offering.id == offering_id)
    )


def get_genre_by_id(db: Session, genre_id: UUID) -> GenreCatalog | None:
    return db.get(GenreCatalog, genre_id)
