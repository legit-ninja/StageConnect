from datetime import UTC, datetime

from app.models.booker_experience import BookerExperienceLevel
from app.models.review import ModerationStatus, Review
from app.services.booker_experience import confirmed_booker_experience_label, booker_experience_warning


def test_booker_experience_ordering() -> None:
    assert BookerExperienceLevel.meets_minimum(1, 3) is False
    assert BookerExperienceLevel.meets_minimum(3, 3) is True
    assert BookerExperienceLevel.meets_minimum(4, 3) is True
    assert BookerExperienceLevel.meets_minimum(None, 3) is True


def test_booker_experience_warning_when_below_minimum() -> None:
    warning = booker_experience_warning(1, 3)
    assert warning is not None
    assert "Beginner" in warning
    assert "Intermediate" in warning


def test_booker_experience_warning_absent_when_null() -> None:
    assert booker_experience_warning(None, 3) is None
    assert booker_experience_warning(2, None) is None


def test_confirmed_skill_requires_two_observations(
    db_session, jazz_genre
) -> None:
    from uuid import uuid4

    from app.models.gig_request import GigRequest, GigStatus, PaymentType
    from tests.conftest import create_user
    from tests.helpers import seed_test_offering

    rider = create_user(db_session, email="rider-skill@test.com", is_booker=True)
    owner1 = create_user(db_session, email="owner1-skill@test.com", is_act_owner=True)
    owner2 = create_user(db_session, email="owner2-skill@test.com", is_act_owner=True)
    offering1 = seed_test_offering(db_session, jazz_genre=jazz_genre, owner=owner1)
    offering2 = seed_test_offering(db_session, jazz_genre=jazz_genre, owner=owner2)

    booking1 = GigRequest(
        offering_id=offering1.id,
        booker_id=rider.id,
        act_owner_id=owner1.id,
        payment_type=PaymentType.PAID,
        status=GigStatus.COMPLETED,
    )
    booking2 = GigRequest(
        offering_id=offering2.id,
        booker_id=rider.id,
        act_owner_id=owner2.id,
        payment_type=PaymentType.PAID,
        status=GigStatus.COMPLETED,
    )
    db_session.add_all([booking1, booking2])
    db_session.flush()

    db_session.add(
        Review(
            gig_request_id=booking1.id,
            reviewer_id=owner1.id,
            reviewee_id=rider.id,
            rating=5,
            observed_booker_experience=3,
            published_at=datetime.now(UTC),
            moderation_status=ModerationStatus.APPROVED,
        )
    )
    db_session.commit()
    assert confirmed_booker_experience_label(db_session, rider.id) is None

    db_session.add(
        Review(
            gig_request_id=booking2.id,
            reviewer_id=owner2.id,
            reviewee_id=rider.id,
            rating=4,
            observed_booker_experience=3,
            published_at=datetime.now(UTC),
            moderation_status=ModerationStatus.APPROVED,
        )
    )
    db_session.commit()
    label = confirmed_booker_experience_label(db_session, rider.id)
    assert label is not None
    assert "Intermediate" in label
