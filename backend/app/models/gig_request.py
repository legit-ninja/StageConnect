import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class PaymentType(str, enum.Enum):
    PAID = "paid"
    FREE = "free"


class GigStatus(str, enum.Enum):
    PENDING_PAYMENT = "pending_payment"
    PENDING_ACT_OWNER = "pending_act_owner"
    COUNTER_OFFERED = "counter_offered"
    APPROVED = "approved"
    COMPLETED = "completed"
    DECLINED = "declined"
    CANCELLED = "cancelled"


class GigRequest(Base):
    __tablename__ = "gig_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    offering_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("offerings.id"), nullable=False, index=True
    )
    booker_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    act_owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    promoter_connection_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("promoter_connections.id"), nullable=True
    )
    payment_type: Mapped[PaymentType] = mapped_column(
        Enum(
            PaymentType,
            name="payment_type",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )
    status: Mapped[GigStatus] = mapped_column(
        Enum(
            GigStatus,
            name="gig_status",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )
    scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    availability_slot_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("offering_availability_slots.id"),
        nullable=True,
        index=True,
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    counter_offer_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    counter_offer_scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    counter_offer_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    confirmed_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    offering = relationship("Offering")
    booker = relationship("User", foreign_keys=[booker_id])
    act_owner = relationship("User", foreign_keys=[act_owner_id])
    promoter_connection = relationship("PromoterConnection")
    availability_slot = relationship("OfferingAvailabilitySlot")
