from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import require_act_owner
from app.models.act import Act
from app.models.offering import Offering
from app.models.offering_availability_slot import OfferingAvailabilitySlot, SlotStatus
from app.models.user import User
from app.schemas.act import ActCreateRequest, ActResponse, ActUpdateRequest
from app.schemas.availability_slot import (
    AvailabilitySlotResponse,
    CreateAvailabilitySlotRequest,
    UpdateAvailabilitySlotRequest,
)
from app.schemas.offering import (
    OfferingCreateRequest,
    OfferingResponse,
    OfferingUpdateRequest,
)
from app.services.events import log_event
from app.services.offerings import get_genre_by_id
from app.config import settings
from app.services.public_location import default_display_location, jitter_coordinates
from app.services.genres import require_act_genres
from app.services.slug import generate_offering_slug

router = APIRouter(prefix="/act-owner", tags=["act-owner"])


def _get_owner_act(db: Session, act_owner_id: UUID, act_id: UUID) -> Act | None:
    return db.scalar(
        select(Act).where(Act.id == act_id, Act.act_owner_id == act_owner_id)
    )


def _get_owner_offering(db: Session, act_owner_id: UUID, offering_id: UUID) -> Offering | None:
    return db.scalar(
        select(Offering).where(Offering.id == offering_id, Offering.act_owner_id == act_owner_id)
    )


@router.get("/acts", response_model=list[ActResponse])
def list_owner_acts(
    db: Session = Depends(get_db),
    host: User = Depends(require_act_owner),
) -> list[Act]:
    # Authz: verified host (owner or trainer) may list only their own acts.
    return list(
        db.scalars(
            select(Act)
            .where(Act.act_owner_id == host.id)
            .order_by(Act.created_at.desc())
        ).all()
    )


@router.post("/acts", response_model=ActResponse, status_code=status.HTTP_201_CREATED)
def create_owner_act(
    payload: ActCreateRequest,
    db: Session = Depends(get_db),
    host: User = Depends(require_act_owner),
) -> Act:
    # Authz: verified owner may create acts they own.
    genre = get_genre_by_id(db, payload.genre_id)
    if genre is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid genre")

    genres = require_act_genres(
        genre, [style.value for style in payload.genres]
    )

    act = Act(
        act_owner_id=host.id,
        genre_id=payload.genre_id,
        name=payload.name,
        act_type=payload.act_type,
        years_active=payload.years_active,
        description=payload.description,
        lat=payload.lat,
        lng=payload.lng,
        address=payload.address,
        photo_urls=payload.photo_urls,
        genres=genres,
    )
    db.add(act)
    db.commit()
    db.refresh(act)
    return act


@router.get("/acts/{act_id}", response_model=ActResponse)
def get_owner_act(
    act_id: UUID,
    db: Session = Depends(get_db),
    host: User = Depends(require_act_owner),
) -> Act:
    # Authz: verified owner may read only their own act.
    act = _get_owner_act(db, host.id, act_id)
    if act is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Act not found")
    return act


@router.patch("/acts/{act_id}", response_model=ActResponse)
def update_owner_act(
    act_id: UUID,
    payload: ActUpdateRequest,
    db: Session = Depends(get_db),
    host: User = Depends(require_act_owner),
) -> Act:
    # Authz: verified owner may update only their own act.
    act = _get_owner_act(db, host.id, act_id)
    if act is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Act not found")

    genre = get_genre_by_id(db, payload.genre_id) if payload.genre_id is not None else get_genre_by_id(db, act.genre_id)
    if genre is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid genre")

    if payload.genre_id is not None:
        act.genre_id = payload.genre_id
    if payload.name is not None:
        act.name = payload.name
    if payload.act_type is not None:
        act.act_type = payload.act_type
    if payload.years_active is not None:
        act.years_active = payload.years_active
    if payload.description is not None:
        act.description = payload.description
    if payload.lat is not None:
        act.lat = payload.lat
    if payload.lng is not None:
        act.lng = payload.lng
    if payload.address is not None:
        act.address = payload.address
    if payload.photo_urls is not None:
        act.photo_urls = payload.photo_urls
    if payload.genres is not None:
        act.genres = require_act_genres(
            genre, [style.value for style in payload.genres]
        )
    elif not (act.genres or []):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Acts require at least one genre",
        )

    db.commit()
    db.refresh(act)
    return act


@router.delete("/acts/{act_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_owner_act(
    act_id: UUID,
    db: Session = Depends(get_db),
    host: User = Depends(require_act_owner),
) -> None:
    # Authz: verified owner may delete only their own act.
    act = _get_owner_act(db, host.id, act_id)
    if act is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Act not found")
    db.delete(act)
    db.commit()


@router.get("/offerings", response_model=list[OfferingResponse])
def list_owner_offerings(
    db: Session = Depends(get_db),
    host: User = Depends(require_act_owner),
) -> list[Offering]:
    # Authz: verified owner may list only their own offerings (including inactive).
    return list(
        db.scalars(
            select(Offering)
            .where(Offering.act_owner_id == host.id)
            .order_by(Offering.created_at.desc())
        ).all()
    )


@router.post("/offerings", response_model=OfferingResponse, status_code=status.HTTP_201_CREATED)
def create_owner_offering(
    payload: OfferingCreateRequest,
    db: Session = Depends(get_db),
    host: User = Depends(require_act_owner),
) -> Offering:
    # Authz: verified owner may create offerings for acts they own.
    act = _get_owner_act(db, host.id, payload.act_id)
    if act is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid act")

    display_location = payload.display_location or default_display_location(act.address)
    pub_lat, pub_lng = jitter_coordinates(
        act.id, act.lat, act.lng, settings.service_area_default_secret
    )

    for _ in range(5):
        offering = Offering(
            act_id=payload.act_id,
            act_owner_id=host.id,
            activity_type=payload.activity_type,
            price=payload.price,
            availability=payload.availability,
            promoter_only_allowed=payload.promoter_only_allowed,
            active=payload.active,
            slug=generate_offering_slug(act.name),
            display_location=display_location,
            public_lat=pub_lat,
            public_lng=pub_lng,
            min_booker_experience=payload.min_booker_experience,
            max_venue_capacity=payload.max_venue_capacity,
            sound_system_required=payload.sound_system_required,
            equipment_provided=payload.equipment_provided,
        )
        db.add(offering)
        try:
            db.commit()
            db.refresh(offering)
            return offering
        except IntegrityError:
            db.rollback()

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Could not generate unique offering slug",
    )


@router.get("/offerings/{offering_id}", response_model=OfferingResponse)
def get_owner_offering(
    offering_id: UUID,
    db: Session = Depends(get_db),
    host: User = Depends(require_act_owner),
) -> Offering:
    # Authz: verified owner may read only their own offering.
    offering = _get_owner_offering(db, host.id, offering_id)
    if offering is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offering not found")
    return offering


@router.patch("/offerings/{offering_id}", response_model=OfferingResponse)
def update_owner_offering(
    offering_id: UUID,
    payload: OfferingUpdateRequest,
    db: Session = Depends(get_db),
    host: User = Depends(require_act_owner),
) -> Offering:
    # Authz: verified owner may update only their own offering.
    offering = _get_owner_offering(db, host.id, offering_id)
    if offering is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offering not found")

    if payload.activity_type is not None:
        offering.activity_type = payload.activity_type
    if payload.price is not None:
        offering.price = payload.price
    if payload.availability is not None:
        offering.availability = payload.availability
    if payload.promoter_only_allowed is not None:
        offering.promoter_only_allowed = payload.promoter_only_allowed
    if payload.active is not None:
        offering.active = payload.active
    if payload.min_booker_experience is not None:
        offering.min_booker_experience = payload.min_booker_experience
    if payload.max_venue_capacity is not None:
        offering.max_venue_capacity = payload.max_venue_capacity
    if payload.sound_system_required is not None:
        offering.sound_system_required = payload.sound_system_required
    if payload.equipment_provided is not None:
        offering.equipment_provided = payload.equipment_provided

    db.commit()
    db.refresh(offering)
    return offering


@router.delete("/offerings/{offering_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_owner_offering(
    offering_id: UUID,
    db: Session = Depends(get_db),
    host: User = Depends(require_act_owner),
) -> None:
    # Authz: verified owner may delete only their own offering.
    offering = _get_owner_offering(db, host.id, offering_id)
    if offering is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offering not found")
    db.delete(offering)
    db.commit()


@router.get("/offerings/{offering_id}/slots", response_model=list[AvailabilitySlotResponse])
def list_offering_slots(
    offering_id: UUID,
    from_date: datetime | None = Query(default=None, alias="from"),
    to_date: datetime | None = Query(default=None, alias="to"),
    db: Session = Depends(get_db),
    host: User = Depends(require_act_owner),
) -> list[OfferingAvailabilitySlot]:
    # Authz: verified owner may list slots for their own offering.
    offering = _get_owner_offering(db, host.id, offering_id)
    if offering is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offering not found")

    stmt = select(OfferingAvailabilitySlot).where(
        OfferingAvailabilitySlot.offering_id == offering_id
    )
    if from_date is not None:
        stmt = stmt.where(OfferingAvailabilitySlot.start_at >= from_date)
    if to_date is not None:
        stmt = stmt.where(OfferingAvailabilitySlot.start_at <= to_date)
    return list(
        db.scalars(stmt.order_by(OfferingAvailabilitySlot.start_at.asc())).all()
    )


@router.post(
    "/offerings/{offering_id}/slots",
    response_model=AvailabilitySlotResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_offering_slot(
    offering_id: UUID,
    payload: CreateAvailabilitySlotRequest,
    db: Session = Depends(get_db),
    host: User = Depends(require_act_owner),
) -> OfferingAvailabilitySlot:
    # Authz: verified owner may create slots for their own offering.
    offering = _get_owner_offering(db, host.id, offering_id)
    if offering is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offering not found")
    if payload.start_at <= datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slot start must be in the future",
        )

    slot = OfferingAvailabilitySlot(
        offering_id=offering.id,
        start_at=payload.start_at,
        end_at=payload.end_at,
        capacity=payload.capacity,
        status=SlotStatus.OPEN,
    )
    db.add(slot)
    db.flush()
    log_event(
        db,
        "slot_created",
        user_id=host.id,
        payload={"slot_id": str(slot.id), "offering_id": str(offering.id)},
    )
    db.commit()
    db.refresh(slot)
    return slot


@router.patch(
    "/offerings/{offering_id}/slots/{slot_id}",
    response_model=AvailabilitySlotResponse,
)
def update_offering_slot(
    offering_id: UUID,
    slot_id: UUID,
    payload: UpdateAvailabilitySlotRequest,
    db: Session = Depends(get_db),
    host: User = Depends(require_act_owner),
) -> OfferingAvailabilitySlot:
    # Authz: verified owner may update open/blocked slots on their offering.
    offering = _get_owner_offering(db, host.id, offering_id)
    if offering is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offering not found")

    slot = db.scalar(
        select(OfferingAvailabilitySlot).where(
            OfferingAvailabilitySlot.id == slot_id,
            OfferingAvailabilitySlot.offering_id == offering_id,
        )
    )
    if slot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slot not found")
    if slot.status in (SlotStatus.HELD, SlotStatus.BOOKED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify a held or booked slot",
        )

    if payload.start_at is not None:
        slot.start_at = payload.start_at
    if payload.end_at is not None:
        slot.end_at = payload.end_at
    if payload.status is not None:
        slot.status = SlotStatus(payload.status)

    log_event(
        db,
        "slot_updated",
        user_id=host.id,
        payload={"slot_id": str(slot.id), "offering_id": str(offering.id)},
    )
    db.commit()
    db.refresh(slot)
    return slot


@router.delete(
    "/offerings/{offering_id}/slots/{slot_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_offering_slot(
    offering_id: UUID,
    slot_id: UUID,
    db: Session = Depends(get_db),
    host: User = Depends(require_act_owner),
) -> None:
    # Authz: verified owner may delete open/blocked slots on their offering.
    offering = _get_owner_offering(db, host.id, offering_id)
    if offering is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offering not found")

    slot = db.scalar(
        select(OfferingAvailabilitySlot).where(
            OfferingAvailabilitySlot.id == slot_id,
            OfferingAvailabilitySlot.offering_id == offering_id,
        )
    )
    if slot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slot not found")
    if slot.status == SlotStatus.BOOKED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a booked slot",
        )

    log_event(
        db,
        "slot_deleted",
        user_id=host.id,
        payload={"slot_id": str(slot.id), "offering_id": str(offering.id)},
    )
    db.delete(slot)
    db.commit()
