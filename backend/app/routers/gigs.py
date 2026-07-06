from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.dependencies import get_current_user, require_admin, require_booker, require_verified
from app.models.gig_request import GigRequest, GigStatus, PaymentType
from app.models.offering import Offering
from app.models.offering_availability_slot import OfferingAvailabilitySlot, SlotStatus
from app.models.message import Message
from app.models.thread import Thread
from app.models.user import User
from app.routers.promoter_connections import get_active_promoter_connection
from app.schemas.gig import (
    GigListResponse,
    GigResponse,
    CreateGigRequest,
    UpdateGigStatusRequest,
)

from app.services.calendar import get_slot_for_booking, mark_slot_booked, recorporate_slot
from app.services.events import log_event
from app.services.flags import maybe_flag_manager_minor_skew
from app.services.booker_experience import booker_experience_warning
from app.services.gig_lifecycle import (
    assert_booker_may_confirm_gig,
    build_confirmed_snapshot,
    confirmed_price,
    confirmed_scheduled_at,
)
from app.services.payments import record_booker_platform_deposit
from app.services.threads import create_gig_thread

router = APIRouter(tags=["gigs"])

INQUIRY_NOTE_MIN_LENGTH = 10


def _thread_id_for_booking(db: Session, booking: GigRequest) -> UUID | None:
    return db.scalar(select(Thread.id).where(Thread.gig_request_id == booking.id))


def _booking_to_response(
    db: Session, booking: GigRequest, *, for_owner: bool = False
) -> GigResponse:
    offering = booking.offering
    warning = None
    if for_owner:
        warning = booker_experience_warning(
            booking.booker.booker_experience_level,
            offering.min_booker_experience,
        )
    display_price = (
        booking.counter_offer_price
        if booking.status == GigStatus.COUNTER_OFFERED and booking.counter_offer_price is not None
        else offering.price
    )
    return GigResponse(
        id=booking.id,
        offering_id=booking.offering_id,
        act_name=offering.act.name,
        booker_id=booking.booker_id,
        rider_email=booking.booker.email,
        rider_verification_status=booking.booker.verification_status.value,
        act_owner_id=booking.act_owner_id,
        act_owner_email=booking.act_owner.email,
        payment_type=booking.payment_type.value,
        status=booking.status.value,
        scheduled_at=booking.scheduled_at,
        availability_slot_id=booking.availability_slot_id,
        note=booking.note,
        requested_at=booking.requested_at,
        offering_price=display_price,
        activity_type=offering.activity_type.value,
        thread_id=_thread_id_for_booking(db, booking),
        booker_experience_warning=warning,
        counter_offer_price=booking.counter_offer_price,
        counter_offer_scheduled_at=booking.counter_offer_scheduled_at,
        counter_offer_note=booking.counter_offer_note,
        confirmed_snapshot=booking.confirmed_snapshot,
    )


def _load_booking(db: Session, booking_id: UUID) -> GigRequest | None:
    return db.scalar(
        select(GigRequest)
        .options(
            selectinload(GigRequest.offering).selectinload(Offering.act),
            selectinload(GigRequest.booker),
            selectinload(GigRequest.act_owner),
        )
        .where(GigRequest.id == booking_id)
    )


def _prepare_booking_context(
    payload: CreateGigRequest,
    db: Session,
    rider: User,
) -> tuple[Offering, PaymentType, UUID | None, OfferingAvailabilitySlot | None, datetime | None, GigStatus, str | None]:
    offering = db.scalar(
        select(Offering)
        .options(selectinload(Offering.act))
        .where(Offering.id == payload.offering_id, Offering.active.is_(True))
    )
    if offering is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offering not found")
    if offering.act_owner_id == rider.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot book your own offering",
        )

    assert_booker_may_confirm_gig(rider, offering)

    is_inquiry = payload.availability_slot_id is None
    if is_inquiry:
        note = (payload.note or "").strip()
        if len(note) < INQUIRY_NOTE_MIN_LENGTH:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Inquiry requires a message of at least {INQUIRY_NOTE_MIN_LENGTH} characters",
            )
    else:
        note = payload.note

    payment_type = PaymentType.FREE if offering.promoter_only_allowed else PaymentType.PAID
    promoter_connection_id = None

    if payment_type == PaymentType.FREE:
        invite = get_active_promoter_connection(db, offering.act_owner_id, rider.id)
        if invite is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Verified friend connection required for this offering",
            )
        promoter_connection_id = invite.id

    slot: OfferingAvailabilitySlot | None = None
    scheduled_at = None
    if payload.availability_slot_id is not None:
        slot = get_slot_for_booking(db, payload.availability_slot_id, offering.id)
        if slot is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Availability slot is not open for this offering",
            )
        slot_start = slot.start_at
        if slot_start.tzinfo is None:
            slot_start = slot_start.replace(tzinfo=UTC)
        if slot_start <= datetime.now(UTC):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Availability slot must be in the future",
            )
        scheduled_at = slot.start_at
        initial_status = (
            GigStatus.PENDING_ACT_OWNER
            if payment_type == PaymentType.FREE
            else GigStatus.PENDING_PAYMENT
        )
    else:
        initial_status = GigStatus.PENDING_ACT_OWNER

    return offering, payment_type, promoter_connection_id, slot, scheduled_at, initial_status, note


def _confirm_gig(
    db: Session,
    booking: GigRequest,
    offering: Offering,
    actor: User,
) -> None:
    assert_booker_may_confirm_gig(booking.booker, offering)
    booking.confirmed_snapshot = build_confirmed_snapshot(booking, offering)
    booking.scheduled_at = confirmed_scheduled_at(booking)
    booking.status = GigStatus.APPROVED
    if booking.availability_slot_id:
        slot = db.get(OfferingAvailabilitySlot, booking.availability_slot_id)
        mark_slot_booked(db, slot)
    record_booker_platform_deposit(db, booking, confirmed_price(booking, offering))
    maybe_flag_manager_minor_skew(db, booking.act_owner_id)
    log_event(
        db,
        "gig_confirmed",
        user_id=actor.id,
        payload={"booking_id": str(booking.id)},
    )


def _apply_status_update(
    db: Session,
    booking: GigRequest,
    payload: UpdateGigStatusRequest,
    actor: User,
) -> GigRequest:
    offering = booking.offering
    is_owner = actor.id == booking.act_owner_id
    is_booker = actor.id == booking.booker_id

    if payload.status == "counter_offer":
        if not is_owner:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Act owner access required")
        if booking.status not in (GigStatus.PENDING_ACT_OWNER, GigStatus.PENDING_PAYMENT):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Booking cannot receive a counter-offer in current status",
            )
        booking.counter_offer_price = payload.counter_offer_price or offering.price
        booking.counter_offer_scheduled_at = payload.counter_offer_scheduled_at or booking.scheduled_at
        booking.counter_offer_note = payload.counter_offer_note
        booking.status = GigStatus.COUNTER_OFFERED
        return booking

    if payload.status == "approved":
        if booking.status == GigStatus.COUNTER_OFFERED:
            if not is_booker:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only the booker may accept a counter-offer",
                )
            _confirm_gig(db, booking, offering, actor)
            return booking
        if not is_owner:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Act owner access required")
        if booking.status not in (GigStatus.PENDING_ACT_OWNER, GigStatus.PENDING_PAYMENT):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Booking cannot be approved in current status",
            )
        _confirm_gig(db, booking, offering, actor)
        return booking

    if not is_owner:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Act owner access required")

    if payload.status == "declined":
        booking.status = GigStatus.DECLINED
        if booking.availability_slot_id:
            slot = db.get(OfferingAvailabilitySlot, booking.availability_slot_id)
            recorporate_slot(db, slot)
    elif payload.status == "cancelled":
        booking.status = GigStatus.CANCELLED
        if booking.availability_slot_id:
            slot = db.get(OfferingAvailabilitySlot, booking.availability_slot_id)
            recorporate_slot(db, slot)
    elif payload.status == "completed":
        if booking.status != GigStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only approved bookings can be marked completed",
            )
        booking.status = GigStatus.COMPLETED
        booking.completed_at = datetime.now(UTC)
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")
    return booking


@router.post("/gigs", response_model=GigResponse, status_code=status.HTTP_201_CREATED)
def create_booking(
    payload: CreateGigRequest,
    db: Session = Depends(get_db),
    rider: User = Depends(require_booker),
) -> GigResponse:
    if rider.is_minor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Minor accounts require a verified guardian before ride activity",
        )

    (
        offering,
        payment_type,
        promoter_connection_id,
        slot,
        scheduled_at,
        initial_status,
        note,
    ) = _prepare_booking_context(payload, db, rider)

    booking = GigRequest(
        offering_id=offering.id,
        booker_id=rider.id,
        act_owner_id=offering.act_owner_id,
        promoter_connection_id=promoter_connection_id,
        payment_type=payment_type,
        status=initial_status,
        scheduled_at=scheduled_at,
        availability_slot_id=payload.availability_slot_id,
        note=note,
    )
    db.add(booking)
    if slot is not None:
        slot.status = SlotStatus.HELD
    db.flush()

    thread = create_gig_thread(db, booking.id)
    message_body = (note if payload.availability_slot_id is None else (payload.note or "")).strip()
    if message_body:
        db.add(Message(thread_id=thread.id, sender_id=rider.id, body=message_body))

    log_event(db, "gig_requested", user_id=rider.id, payload={"booking_id": str(booking.id)})
    maybe_flag_manager_minor_skew(db, offering.act_owner_id)
    db.commit()
    loaded = _load_booking(db, booking.id)
    assert loaded is not None
    return _booking_to_response(db, loaded, for_owner=False)


@router.get("/gigs", response_model=GigListResponse)
def list_bookings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified),
    role: str = Query(default="rider", pattern="^(rider|owner)$"),
) -> GigListResponse:
    if role == "owner":
        if not current_user.is_act_owner:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Act owner access required",
            )
        stmt = select(GigRequest).where(GigRequest.act_owner_id == current_user.id)
    else:
        stmt = select(GigRequest).where(GigRequest.booker_id == current_user.id)

    bookings = list(
        db.scalars(
            stmt.options(
                selectinload(GigRequest.offering).selectinload(Offering.act),
                selectinload(GigRequest.booker),
                selectinload(GigRequest.act_owner),
            ).order_by(GigRequest.requested_at.desc())
        ).all()
    )

    return GigListResponse(
        items=[
            _booking_to_response(db, b, for_owner=(role == "owner"))
            for b in bookings
        ],
        total=len(bookings),
    )


@router.patch("/gigs/{booking_id}", response_model=GigResponse)
def update_gig_status(
    booking_id: UUID,
    payload: UpdateGigStatusRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
) -> GigResponse:
    booking = _load_booking(db, booking_id)
    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    if actor.id not in (booking.act_owner_id, booking.booker_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    _apply_status_update(db, booking, payload, actor)

    db.commit()
    loaded = _load_booking(db, booking.id)
    assert loaded is not None
    for_owner = actor.id == booking.act_owner_id
    return _booking_to_response(db, loaded, for_owner=for_owner)


@router.get("/admin/gigs", response_model=GigListResponse)
def admin_list_bookings(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> GigListResponse:
    total = db.scalar(select(func.count()).select_from(GigRequest)) or 0
    bookings = list(
        db.scalars(
            select(GigRequest)
            .options(
                selectinload(GigRequest.offering).selectinload(Offering.act),
                selectinload(GigRequest.booker),
                selectinload(GigRequest.act_owner),
            )
            .order_by(GigRequest.requested_at.desc())
            .limit(limit)
            .offset(offset)
        ).all()
    )
    return GigListResponse(
        items=[_booking_to_response(db, b) for b in bookings],
        total=total,
    )
