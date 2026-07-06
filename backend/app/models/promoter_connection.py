import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class PromoterConnectionStatus(str, enum.Enum):
    PENDING_ACT_OWNER_CONFIRM = "pending_act_owner_confirm"
    PENDING_GUARDIAN = "pending_guardian"
    ACTIVE = "active"
    DECLINED = "declined"
    REVOKED = "revoked"


class PromoterConnection(Base):
    __tablename__ = "promoter_connections"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    act_owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    booker_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )
    invite_token_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invite_tokens.id"), nullable=True
    )
    invitee_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[PromoterConnectionStatus] = mapped_column(
        Enum(
            PromoterConnectionStatus,
            name="promoter_connection_status",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        default=PromoterConnectionStatus.PENDING_ACT_OWNER_CONFIRM,
    )
    invited_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    owner_confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    guardian_approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    owner = relationship("User", foreign_keys=[act_owner_id])
    rider = relationship("User", foreign_keys=[booker_id])
    invite_token = relationship("InviteToken", foreign_keys=[invite_token_id])
