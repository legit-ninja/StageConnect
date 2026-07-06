import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class TransactionDirection(str, enum.Enum):
    BOOKER_TO_PLATFORM_DEPOSIT = "booker_to_platform_deposit"


class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    gig_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("gig_requests.id"), nullable=False, index=True
    )
    booker_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    direction: Mapped[TransactionDirection] = mapped_column(
        Enum(
            TransactionDirection,
            name="transaction_direction",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    stripe_payment_intent_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    gig_request = relationship("GigRequest", foreign_keys=[gig_request_id])
    booker = relationship("User", foreign_keys=[booker_id])
