from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.act import Act
from app.models.gig_request import GigRequest
from app.models.offering import Offering
from app.models.offering_photo import OfferingPhoto
from app.models.review import ModerationStatus, Review
from app.models.booker_experience import BookerExperienceLevel
from app.models.user import VerificationStatus
from app.schemas.public_offering import PublicOffering, equipment_provided_label
from app.services.storage import get_public_url


def _owner_last_initial(last_name: str) -> str:
    return last_name[:1].upper() if last_name else ""


def _photo_urls_for_offering(db: Session, offering: Offering) -> list[str]:
    photos = list(
        db.scalars(
            select(OfferingPhoto)
            .where(
                OfferingPhoto.offering_id == offering.id,
                OfferingPhoto.moderation_status == ModerationStatus.APPROVED,
            )
            .order_by(OfferingPhoto.is_primary.desc(), OfferingPhoto.sort_order)
        ).all()
    )
    if photos:
        return [get_public_url(p.storage_key) for p in photos]
    return list(offering.act.photo_urls or [])


def _review_aggregates(db: Session, offering_id) -> tuple[int, float | None]:
    row = db.execute(
        select(func.count(Review.id), func.avg(Review.rating))
        .select_from(Review)
        .join(GigRequest, Review.gig_request_id == GigRequest.id)
        .where(
            GigRequest.offering_id == offering_id,
            Review.published_at.is_not(None),
            Review.moderation_status == ModerationStatus.APPROVED,
        )
    ).one()
    count = int(row[0] or 0)
    average = float(row[1]) if row[1] is not None else None
    return count, average


def offering_to_public(db: Session, offering: Offering) -> PublicOffering:
    act_owner = offering.owner
    act = offering.act
    review_count, review_average = _review_aggregates(db, offering.id)
    member_since = act_owner.created_at.strftime("%B %Y")
    genre_name = act.genre_catalog.name if act.genre_catalog is not None else "jazz"

    return PublicOffering(
        act_name=act.name,
        genre=genre_name,
        act_type=act.act_type,
        years_active=act.years_active,
        photo_urls=_photo_urls_for_offering(db, offering),
        activity_type=offering.activity_type.value,
        price=offering.price if offering.price > 0 else None,
        display_location=offering.display_location,
        public_lat=offering.public_lat,
        public_lng=offering.public_lng,
        act_owner_first_name=act_owner.first_name,
        act_owner_last_initial=_owner_last_initial(act_owner.last_name),
        act_owner_verified=act_owner.verification_status == VerificationStatus.VERIFIED,
        act_owner_member_since=member_since,
        review_count=review_count,
        review_average=round(review_average, 1) if review_average is not None else None,
        slug=offering.slug,
        active=offering.active,
        genres=list(act.genres or []),
        min_booker_experience=offering.min_booker_experience,
        min_booker_experience_label=BookerExperienceLevel.minimum_label(offering.min_booker_experience),
        max_venue_capacity=offering.max_venue_capacity,
        sound_system_required=offering.sound_system_required,
        equipment_provided=offering.equipment_provided.value,
        equipment_provided_label=equipment_provided_label(offering.equipment_provided),
        act_owner_manager_verified=act_owner.manager_verified,
    )


def get_offering_by_slug(db: Session, slug: str) -> Offering | None:
    return db.scalar(
        select(Offering)
        .options(
            selectinload(Offering.act).selectinload(Act.genre_catalog),
            selectinload(Offering.owner),
        )
        .where(Offering.slug == slug)
    )
