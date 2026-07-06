from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.review import ModerationStatus, Review
from app.models.booker_experience import BookerExperienceLevel


def booker_experience_warning(
    rider_level: int | None,
    min_level: int | None,
) -> str | None:
    if min_level is None or rider_level is None:
        return None
    if BookerExperienceLevel.meets_minimum(rider_level, min_level):
        return None
    self_label = BookerExperienceLevel.label(rider_level) or "Unknown"
    min_label = BookerExperienceLevel.minimum_label(min_level) or "a higher level"
    return f"Rider self-reports {self_label}; your offering suggests {min_label}."


def confirmed_booker_experience(db: Session, booker_id) -> tuple[int | None, int]:
    """Mode of published owner-observed skills; requires min 2 distinct owner reviews."""
    rows = db.scalars(
        select(Review.observed_booker_experience).where(
            Review.reviewee_id == booker_id,
            Review.observed_booker_experience.is_not(None),
            Review.published_at.is_not(None),
            Review.moderation_status == ModerationStatus.APPROVED,
        )
    ).all()
    values = [v for v in rows if v is not None]
    if len(values) < 2:
        return None, len(values)
    mode_value, _ = Counter(values).most_common(1)[0]
    return mode_value, len(values)


def confirmed_booker_experience_label(db: Session, booker_id) -> str | None:
    mode, count = confirmed_booker_experience(db, booker_id)
    if mode is None or count < 2:
        return None
    label = BookerExperienceLevel.label(mode)
    if label is None:
        return None
    return f"Confirmed {label} by {count} owners"
