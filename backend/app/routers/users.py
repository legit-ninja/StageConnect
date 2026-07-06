import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import require_verified
from app.models.gig_request import GigRequest, GigStatus
from app.models.promoter_connection import PromoterConnection, PromoterConnectionStatus
from app.models.booker_experience import BookerExperienceLevel
from app.models.user import User
from app.schemas.counterparty import CounterpartyProfile
from app.services.booker_experience import confirmed_booker_experience_label

router = APIRouter(prefix="/users", tags=["users"])


def _has_counterparty_relationship(db: Session, viewer_id: uuid.UUID, target_id: uuid.UUID) -> bool:
    booking_exists = db.scalar(
        select(GigRequest.id)
        .where(
            or_(
                (
                    (GigRequest.booker_id == viewer_id)
                    & (GigRequest.act_owner_id == target_id)
                ),
                (
                    (GigRequest.booker_id == target_id)
                    & (GigRequest.act_owner_id == viewer_id)
                ),
            ),
            GigRequest.status.in_(
                (
                    GigStatus.APPROVED,
                    GigStatus.COMPLETED,
                    GigStatus.PENDING_ACT_OWNER,
                    GigStatus.PENDING_PAYMENT,
                )
            ),
        )
        .limit(1)
    )
    if booking_exists is not None:
        return True
    invite_exists = db.scalar(
        select(PromoterConnection.id)
        .where(
            or_(
                (
                    (PromoterConnection.act_owner_id == viewer_id)
                    & (PromoterConnection.booker_id == target_id)
                ),
                (
                    (PromoterConnection.act_owner_id == target_id)
                    & (PromoterConnection.booker_id == viewer_id)
                ),
            ),
            PromoterConnection.status == PromoterConnectionStatus.ACTIVE,
        )
        .limit(1)
    )
    return invite_exists is not None


def _trainer_labels(user: User) -> list[str]:
    labels: list[str] = []
    if user.is_act_manager:
        labels.append("Self-reported: Band trainer")
    if user.is_booking_coordinator:
        labels.append("Self-reported: Riding instructor")
    return labels


@router.get("/{user_id}/counterparty", response_model=CounterpartyProfile)
def get_counterparty_profile(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified),
) -> CounterpartyProfile:
    # Authz: verified users may view skill/trainer self-reports only for active connections.
    if user_id == current_user.id:
        target = current_user
    else:
        if not _has_counterparty_relationship(db, current_user.id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not connected to this user",
            )
        target = db.get(User, user_id)
        if target is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    last_initial = target.last_name[:1].upper() if target.last_name else ""
    return CounterpartyProfile(
        id=target.id,
        first_name=target.first_name,
        last_initial=last_initial,
        self_reported_skill_label=BookerExperienceLevel.self_reported_label(target.booker_experience_level),
        confirmed_skill_label=confirmed_booker_experience_label(db, target.id),
        is_act_manager=target.is_act_manager,
        is_booking_coordinator=target.is_booking_coordinator,
        manager_verified=target.manager_verified,
        manager_self_report_labels=_trainer_labels(target),
    )
