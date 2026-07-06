from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException, status

from app.models.gig_request import GigRequest
from app.models.offering import Offering
from app.models.user import User


def assert_booker_may_confirm_gig(booker: User, offering: Offering) -> None:
    if booker.is_minor and offering.requires_21_plus:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Minor accounts cannot confirm 21+ venue gigs",
        )


def confirmed_price(booking: GigRequest, offering: Offering) -> Decimal:
    if booking.counter_offer_price is not None:
        return booking.counter_offer_price
    return offering.price


def confirmed_scheduled_at(booking: GigRequest) -> datetime | None:
    if booking.counter_offer_scheduled_at is not None:
        return booking.counter_offer_scheduled_at
    return booking.scheduled_at


def build_confirmed_snapshot(booking: GigRequest, offering: Offering) -> dict:
    price = confirmed_price(booking, offering)
    scheduled_at = confirmed_scheduled_at(booking)
    return {
        "offering_id": str(offering.id),
        "act_name": offering.act.name,
        "activity_type": offering.activity_type.value,
        "price": str(price),
        "scheduled_at": scheduled_at.isoformat() if scheduled_at else None,
        "payment_type": booking.payment_type.value,
        "requires_21_plus": offering.requires_21_plus,
        "counter_offer_note": booking.counter_offer_note,
    }
