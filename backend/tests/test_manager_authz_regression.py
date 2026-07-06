from app.models.user import VerificationStatus
from tests.helpers import seed_test_offering


def test_trainer_without_owner_cannot_manage_slots(client, db_session, jazz_genre) -> None:
    from datetime import UTC, datetime, timedelta

    from tests.conftest import auth_header, create_user

    owner = create_user(
        db_session,
        email="owner-slots@example.com",
        is_act_owner=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    trainer = create_user(
        db_session,
        email="trainer-slots@example.com",
        is_booking_coordinator=True,
        is_act_owner=False,
        verification_status=VerificationStatus.VERIFIED,
    )
    offering = seed_test_offering(db_session, jazz_genre=jazz_genre, owner=owner)

    start = datetime.now(UTC) + timedelta(days=3)
    end = start + timedelta(hours=2)
    create_resp = client.post(
        f"/act-owner/offerings/{offering.id}/slots",
        headers=auth_header(trainer),
        json={"start_at": start.isoformat(), "end_at": end.isoformat()},
    )
    assert create_resp.status_code == 403


def test_trainer_without_owner_cannot_create_offering(client, db_session, jazz_genre) -> None:
    from tests.conftest import auth_header, create_user

    owner = create_user(
        db_session,
        email="owner-acts@example.com",
        is_act_owner=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    trainer = create_user(
        db_session,
        email="trainer-offering@example.com",
        is_act_manager=True,
        is_act_owner=False,
        verification_status=VerificationStatus.VERIFIED,
    )
    from app.models.act import Act

    act = Act(
        act_owner_id=owner.id,
        genre_id=jazz_genre.id,
        name="NotMine",
        lat=36.2,
        lng=-81.6,
        address="Boone, NC",
    )
    db_session.add(act)
    db_session.commit()

    response = client.post(
        "/act-owner/offerings",
        headers=auth_header(trainer),
        json={
            "act_id": str(act.id),
            "activity_type": "wedding",
            "price": "50.00",
        },
    )
    assert response.status_code == 403


def test_trainer_without_owner_cannot_view_owner_bookings(client, db_session) -> None:
    from tests.conftest import auth_header, create_user

    trainer = create_user(
        db_session,
        email="trainer-bookings@example.com",
        is_booking_coordinator=True,
        is_act_owner=False,
        verification_status=VerificationStatus.VERIFIED,
    )
    response = client.get(
        "/gigs",
        params={"role": "owner"},
        headers=auth_header(trainer),
    )
    assert response.status_code == 403
