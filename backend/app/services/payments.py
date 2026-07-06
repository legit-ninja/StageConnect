from decimal import Decimal

from sqlalchemy.orm import Session

from app.config import settings
from app.models.gig_request import GigRequest, PaymentType
from app.models.payment_transaction import PaymentTransaction, TransactionDirection


def stripe_enabled() -> bool:
    return settings.payments_enabled and bool(settings.stripe_secret_key.strip())


def record_booker_platform_deposit(
    db: Session,
    booking: GigRequest,
    amount: Decimal,
) -> PaymentTransaction | None:
    """Record a booker→platform deposit when Stripe payments are enabled."""
    if not stripe_enabled():
        return None
    if booking.payment_type != PaymentType.PAID:
        return None
    tx = PaymentTransaction(
        gig_request_id=booking.id,
        booker_id=booking.booker_id,
        direction=TransactionDirection.BOOKER_TO_PLATFORM_DEPOSIT,
        amount=amount,
    )
    db.add(tx)
    return tx
