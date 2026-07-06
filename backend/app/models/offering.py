import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, Numeric, SmallInteger, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class ActivityType(str, enum.Enum):
    PRIVATE_GIG = "private_gig"
    CORPORATE = "corporate"
    WEDDING = "wedding"
    FESTIVAL = "festival"


class EquipmentProvided(str, enum.Enum):
    PROVIDED = "provided"
    BRING_OWN = "bring_own"
    EITHER = "either"


class Offering(Base):
    __tablename__ = "offerings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    act_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("acts.id"), nullable=False, index=True
    )
    act_owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    activity_type: Mapped[ActivityType] = mapped_column(
        Enum(
            ActivityType,
            name="activity_type",
            values_callable=lambda enum: [member.value for member in enum],
        ),
        nullable=False,
    )
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    availability: Mapped[str | None] = mapped_column(Text, nullable=True)
    promoter_only_allowed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    display_location: Mapped[str] = mapped_column(String(256), nullable=False)
    public_lat: Mapped[float] = mapped_column(Float, nullable=False)
    public_lng: Mapped[float] = mapped_column(Float, nullable=False)
    min_booker_experience: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    max_venue_capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sound_system_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    equipment_provided: Mapped[EquipmentProvided] = mapped_column(
        Enum(
            EquipmentProvided,
            name="equipment_provided",
            values_callable=lambda e: [m.value for m in e],
        ),
        default=EquipmentProvided.EITHER,
        nullable=False,
    )
    requires_21_plus: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    act = relationship("Act", back_populates="offerings")
    owner = relationship("User", back_populates="offerings")
    photos = relationship("OfferingPhoto", back_populates="offering")
    availability_slots = relationship(
        "OfferingAvailabilitySlot", back_populates="offering", cascade="all, delete-orphan"
    )
