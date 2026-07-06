from decimal import Decimal

from app.models.offering import ActivityType
from app.models.user import VerificationStatus
from tests.helpers import seed_test_offering


def test_public_offerings_only_active(
    client, db_session, jazz_genre
) -> None:
    from tests.conftest import create_user

    owner = create_user(
        db_session,
        email="owner@example.com",
        is_act_owner=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    seed_test_offering(
        db_session,
        jazz_genre=jazz_genre,
        owner=owner,
        act_name="Star",
        activity_type=ActivityType.WEDDING,
        price=Decimal("50.00"),
        active=True,
    )
    seed_test_offering(
        db_session,
        jazz_genre=jazz_genre,
        owner=owner,
        act_name="Star2",
        activity_type=ActivityType.PRIVATE_GIG,
        price=Decimal("40.00"),
        active=False,
    )

    response = client.get("/offerings")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["act_name"] == "Star"


def test_public_offerings_filter_activity(
    client, db_session, jazz_genre
) -> None:
    from tests.conftest import create_user

    owner = create_user(
        db_session,
        email="owner2@example.com",
        is_act_owner=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    seed_test_offering(
        db_session,
        jazz_genre=jazz_genre,
        owner=owner,
        act_name="Daisy",
        activity_type=ActivityType.WEDDING,
        price=Decimal("50.00"),
        active=True,
    )
    seed_test_offering(
        db_session,
        jazz_genre=jazz_genre,
        owner=owner,
        act_name="Daisy2",
        activity_type=ActivityType.PRIVATE_GIG,
        price=Decimal("40.00"),
        active=True,
    )

    response = client.get("/offerings?activity_type=private_gig")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["activity_type"] == "private_gig"
