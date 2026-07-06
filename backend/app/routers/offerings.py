from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.dependencies import require_booker, require_verified
from app.models.offering import ActivityType
from app.models.genre import Genre
from app.models.user import User
from app.schemas.availability_slot import AvailabilitySlotResponse
from app.schemas.offering import OfferingDetail, OfferingSummary
from app.services.calendar import get_open_slots_for_offering
from app.services.offerings import (
    get_offering_detail,
    offering_to_detail,
    offering_to_summary,
    search_offerings,
)

router = APIRouter(prefix="/offerings", tags=["offerings"])


@router.get("", response_model=list[OfferingSummary])
def list_public_offerings(
    db: Session = Depends(get_db),
    activity_type: ActivityType | None = None,
    genre_id: UUID | None = None,
    min_price: Decimal | None = Query(default=None, ge=0),
    max_price: Decimal | None = Query(default=None, ge=0),
    genre: Genre | None = None,
    lat: float | None = None,
    lng: float | None = None,
    radius_km: float | None = Query(default=None, gt=0),
) -> list[OfferingSummary]:
    # Authz: public read of active offerings only; no auth required.
    offerings = search_offerings(
        db,
        activity_type=activity_type,
        genre_id=genre_id,
        min_price=min_price,
        max_price=max_price,
        genre=genre,
        lat=lat if lat is not None else settings.service_area_default_lat,
        lng=lng if lng is not None else settings.service_area_default_lng,
        radius_km=radius_km if radius_km is not None else settings.service_area_default_radius_km,
        active_only=True,
    )
    return [offering_to_summary(offering) for offering in offerings]


@router.get("/{offering_id}", response_model=OfferingDetail)
def get_offering_detail_authenticated(
    offering_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(require_verified),
) -> OfferingDetail:
    # Authz: verified users may read full offering detail including description.
    offering = get_offering_detail(db, offering_id)
    if offering is None or not offering.active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offering not found")
    return offering_to_detail(offering)


@router.get("/{offering_id}/slots", response_model=list[AvailabilitySlotResponse])
def list_offering_open_slots(
    offering_id: UUID,
    db: Session = Depends(get_db),
    _rider: User = Depends(require_booker),
) -> list[AvailabilitySlotResponse]:
    # Authz: verified riders may view bookable open slots on active offerings.
    offering = get_offering_detail(db, offering_id)
    if offering is None or not offering.active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offering not found")

    slots = get_open_slots_for_offering(db, offering_id)
    return [AvailabilitySlotResponse.model_validate(slot) for slot in slots]
