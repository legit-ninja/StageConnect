from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.act import Act
from app.models.gig_request import GigRequest, GigStatus
from app.models.offering import Offering
from app.models.offering_availability_slot import OfferingAvailabilitySlot, SlotStatus
from app.models.user import User
from app.schemas.availability_slot import (
    CalendarDaySummary,
    CalendarResponse,
    CalendarWeatherDay,
    OpenSlotSummary,
)
from app.schemas.gig import GigResponse
from app.services.offerings import haversine_km
from app.services.weather import DailyWeather, fetch_daily_forecast


def _booking_to_response(booking: GigRequest) -> GigResponse:
    offering = booking.offering
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
        note=booking.note,
        requested_at=booking.requested_at,
        offering_price=offering.price,
        activity_type=offering.activity_type.value,
        availability_slot_id=booking.availability_slot_id,
    )


def _slot_to_open_summary(slot: OfferingAvailabilitySlot) -> OpenSlotSummary:
    offering = slot.offering
    return OpenSlotSummary(
        id=slot.id,
        offering_id=offering.id,
        slug=offering.slug,
        act_name=offering.act.name,
        activity_type=offering.activity_type.value,
        price=offering.price,
        display_location=offering.display_location,
        start_at=slot.start_at,
        end_at=slot.end_at,
    )


def _date_range(from_date: date, to_date: date) -> list[date]:
    days: list[date] = []
    current = from_date
    while current <= to_date:
        days.append(current)
        current += timedelta(days=1)
    return days


def _slot_on_date(slot: OfferingAvailabilitySlot, day: date) -> bool:
    start = slot.start_at.astimezone(UTC).date()
    return start == day


def _booking_on_date(booking: GigRequest, day: date) -> bool:
    if booking.scheduled_at is None:
        return False
    return booking.scheduled_at.astimezone(UTC).date() == day


def get_open_slots_in_range(
    db: Session,
    *,
    from_dt: datetime,
    to_dt: datetime,
    lat: float,
    lng: float,
    radius_km: float,
) -> list[OfferingAvailabilitySlot]:
    stmt = (
        select(OfferingAvailabilitySlot)
        .join(Offering, OfferingAvailabilitySlot.offering_id == Offering.id)
        .options(selectinload(OfferingAvailabilitySlot.offering).selectinload(Offering.act))
        .where(
            Offering.active.is_(True),
            OfferingAvailabilitySlot.status == SlotStatus.OPEN,
            OfferingAvailabilitySlot.start_at >= from_dt,
            OfferingAvailabilitySlot.start_at <= to_dt,
        )
        .order_by(OfferingAvailabilitySlot.start_at.asc())
    )
    slots = list(db.scalars(stmt).all())
    filtered: list[OfferingAvailabilitySlot] = []
    for slot in slots:
        offering = slot.offering
        if haversine_km(lat, lng, offering.public_lat, offering.public_lng) <= radius_km:
            filtered.append(slot)
    return filtered


def get_user_bookings_in_range(
    db: Session,
    user: User,
    *,
    from_dt: datetime,
    to_dt: datetime,
) -> list[GigRequest]:
    active_statuses = (
        GigStatus.PENDING_PAYMENT,
        GigStatus.PENDING_ACT_OWNER,
        GigStatus.APPROVED,
        GigStatus.COMPLETED,
    )
    stmt = (
        select(GigRequest)
        .options(
            selectinload(GigRequest.offering).selectinload(Offering.act),
            selectinload(GigRequest.booker),
            selectinload(GigRequest.act_owner),
        )
        .where(
            GigRequest.status.in_(active_statuses),
            GigRequest.scheduled_at.isnot(None),
            GigRequest.scheduled_at >= from_dt,
            GigRequest.scheduled_at <= to_dt,
            or_(
                GigRequest.booker_id == user.id,
                GigRequest.act_owner_id == user.id,
            ),
        )
        .order_by(GigRequest.scheduled_at.asc())
    )
    return list(db.scalars(stmt).all())


def build_calendar_response(
    db: Session,
    user: User,
    *,
    from_date: date,
    to_date: date,
    lat: float,
    lng: float,
    radius_km: float,
    include_open_slots: bool,
) -> CalendarResponse:
    from_dt = datetime.combine(from_date, datetime.min.time(), tzinfo=UTC)
    to_dt = datetime.combine(to_date, datetime.max.time(), tzinfo=UTC)

    open_slots: list[OfferingAvailabilitySlot] = []
    if include_open_slots and user.is_booker:
        open_slots = get_open_slots_in_range(
            db,
            from_dt=from_dt,
            to_dt=to_dt,
            lat=lat,
            lng=lng,
            radius_km=radius_km,
        )

    my_bookings = get_user_bookings_in_range(db, user, from_dt=from_dt, to_dt=to_dt)

    weather_rows: list[DailyWeather] = []
    weather_error: str | None = None
    try:
        weather_rows = fetch_daily_forecast(lat, lng, from_date, to_date)
        if not weather_rows:
            weather_error = "Weather forecast unavailable"
    except Exception:
        weather_error = "Weather forecast unavailable"

    weather_by_date = {row.date: row for row in weather_rows}

    days: list[CalendarDaySummary] = []
    for day in _date_range(from_date, to_date):
        day_str = day.isoformat()
        weather_row = weather_by_date.get(day_str)
        weather = None
        if weather_row:
            weather = CalendarWeatherDay(
                date=weather_row.date,
                temp_max_f=weather_row.temp_max_f,
                temp_min_f=weather_row.temp_min_f,
                precip_probability_max=weather_row.precip_probability_max,
                wind_speed_max_mph=weather_row.wind_speed_max_mph,
                weather_code=weather_row.weather_code,
                ride_suitability=weather_row.ride_suitability,
                summary=weather_row.summary,
            )
        days.append(
            CalendarDaySummary(
                date=day_str,
                open_slot_count=sum(1 for s in open_slots if _slot_on_date(s, day)),
                my_booking_count=sum(1 for b in my_bookings if _booking_on_date(b, day)),
                weather=weather,
            )
        )

    return CalendarResponse(
        days=days,
        open_slots=[_slot_to_open_summary(s) for s in open_slots],
        my_bookings=[_booking_to_response(b) for b in my_bookings],
        weather_error=weather_error,
    )


def get_open_slots_for_offering(
    db: Session, offering_id: UUID, *, now: datetime | None = None
) -> list[OfferingAvailabilitySlot]:
    if now is None:
        now = datetime.now(UTC)
    return list(
        db.scalars(
            select(OfferingAvailabilitySlot)
            .where(
                OfferingAvailabilitySlot.offering_id == offering_id,
                OfferingAvailabilitySlot.status == SlotStatus.OPEN,
                OfferingAvailabilitySlot.start_at > now,
            )
            .order_by(OfferingAvailabilitySlot.start_at.asc())
        ).all()
    )


def get_slot_for_booking(
    db: Session, slot_id: UUID, offering_id: UUID
) -> OfferingAvailabilitySlot | None:
    return db.scalar(
        select(OfferingAvailabilitySlot).where(
            OfferingAvailabilitySlot.id == slot_id,
            OfferingAvailabilitySlot.offering_id == offering_id,
            OfferingAvailabilitySlot.status == SlotStatus.OPEN,
        )
    )


def recorporate_slot(db: Session, slot: OfferingAvailabilitySlot | None) -> None:
    if slot is None:
        return
    if slot.status in (SlotStatus.HELD, SlotStatus.BOOKED):
        slot.status = SlotStatus.OPEN


def mark_slot_booked(db: Session, slot: OfferingAvailabilitySlot | None) -> None:
    if slot is None:
        return
    slot.status = SlotStatus.BOOKED
