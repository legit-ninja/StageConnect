from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.act import Act
from app.models.offering import Offering
from app.models.oauth_account import OAuthAccount
from app.models.user import User, VerificationStatus
from app.schemas.admin import AdminGuardianSummary, AdminUserDetail, AdminUserSummary


def user_to_summary(user: User) -> AdminUserSummary:
    oauth_providers = [account.provider for account in user.oauth_accounts]
    return AdminUserSummary(
        id=user.id,
        email=user.email,
        is_booker=user.is_booker,
        is_act_owner=user.is_act_owner,
        is_act_manager=user.is_act_manager,
        is_booking_coordinator=user.is_booking_coordinator,
        manager_verified=user.manager_verified,
        is_admin=user.is_admin,
        verification_status=user.verification_status,
        is_minor=user.is_minor,
        booker_experience_level=user.booker_experience_level,
        oauth_providers=oauth_providers,
        created_at=user.created_at,
    )


def _guardian_summary(user: User) -> AdminGuardianSummary | None:
    if user.guardian is None:
        return None
    return AdminGuardianSummary(
        id=user.guardian.id,
        email=user.guardian.email,
        verification_status=user.guardian.verification_status,
    )


def user_to_detail(
    user: User,
    *,
    act_count: int = 0,
    offering_count: int = 0,
    active_offering_count: int = 0,
) -> AdminUserDetail:
    summary = user_to_summary(user)
    return AdminUserDetail(
        **summary.model_dump(),
        phone=user.phone,
        guardian_user_id=user.guardian_user_id,
        guardian=_guardian_summary(user),
        oauth_accounts=list(user.oauth_accounts),
        act_count=act_count,
        offering_count=offering_count,
        active_offering_count=active_offering_count,
    )


def get_user_detail(db: Session, user_id: UUID) -> User | None:
    return db.scalar(
        select(User)
        .options(
            selectinload(User.oauth_accounts),
            selectinload(User.guardian),
        )
        .where(User.id == user_id)
    )


def get_user_marketplace_counts(
    db: Session, user_id: UUID
) -> tuple[int, int, int]:
    act_count = (
        db.scalar(
            select(func.count()).select_from(Act).where(Act.act_owner_id == user_id)
        )
        or 0
    )
    offering_count = (
        db.scalar(
            select(func.count()).select_from(Offering).where(Offering.act_owner_id == user_id)
        )
        or 0
    )
    active_offering_count = (
        db.scalar(
            select(func.count())
            .select_from(Offering)
            .where(Offering.act_owner_id == user_id, Offering.active.is_(True))
        )
        or 0
    )
    return act_count, offering_count, active_offering_count


def list_users(
    db: Session,
    *,
    q: str | None,
    verification_status: VerificationStatus | None,
    is_admin: bool | None,
    limit: int,
    offset: int,
) -> tuple[list[User], int]:
    base = select(User).options(selectinload(User.oauth_accounts))
    count_query = select(func.count()).select_from(User)

    if q:
        pattern = f"%{q.strip().lower()}%"
        email_filter = func.lower(User.email).like(pattern)
        base = base.where(email_filter)
        count_query = count_query.where(email_filter)

    if verification_status is not None:
        base = base.where(User.verification_status == verification_status)
        count_query = count_query.where(User.verification_status == verification_status)

    if is_admin is not None:
        base = base.where(User.is_admin.is_(is_admin))
        count_query = count_query.where(User.is_admin.is_(is_admin))

    total = db.scalar(count_query) or 0
    users = list(
        db.scalars(
            base.order_by(User.created_at.desc()).limit(limit).offset(offset)
        ).all()
    )
    return users, total


def count_oauth_users(db: Session) -> int:
    return (
        db.scalar(
            select(func.count(func.distinct(OAuthAccount.user_id))).select_from(
                OAuthAccount
            )
        )
        or 0
    )


def count_signups_since(db: Session, since: datetime) -> int:
    return (
        db.scalar(
            select(func.count()).select_from(User).where(User.created_at >= since)
        )
        or 0
    )


def count_by_verification(db: Session, status: VerificationStatus) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(User)
            .where(User.verification_status == status)
        )
        or 0
    )
