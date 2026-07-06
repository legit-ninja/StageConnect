from app.models.user import VerificationStatus
from tests.helpers import seed_test_offering


def test_thread_messages_round_trip(client, db_session, jazz_genre) -> None:
    from tests.conftest import auth_header, create_user

    owner = create_user(
        db_session,
        email="owner-thread@example.com",
        is_act_owner=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    rider = create_user(
        db_session,
        email="rider-thread@example.com",
        is_booker=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    offering = seed_test_offering(db_session, jazz_genre=jazz_genre, owner=owner)

    create_resp = client.post(
        "/gigs",
        headers=auth_header(rider),
        json={
            "offering_id": str(offering.id),
            "note": "Hello, are you available next month?",
        },
    )
    thread_id = create_resp.json()["thread_id"]
    assert thread_id is not None

    list_resp = client.get(f"/threads/{thread_id}/messages", headers=auth_header(owner))
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 1

    post_resp = client.post(
        f"/threads/{thread_id}/messages",
        headers=auth_header(owner),
        json={"body": "Thanks for reaching out — I will add slots soon."},
    )
    assert post_resp.status_code == 201

    list_resp2 = client.get(f"/threads/{thread_id}/messages", headers=auth_header(rider))
    assert list_resp2.json()["total"] == 2


def test_non_participant_cannot_read_thread(client, db_session, jazz_genre) -> None:
    from tests.conftest import auth_header, create_user

    owner = create_user(
        db_session,
        email="owner-thread2@example.com",
        is_act_owner=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    rider = create_user(
        db_session,
        email="rider-thread2@example.com",
        is_booker=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    outsider = create_user(
        db_session,
        email="outsider-thread@example.com",
        is_booker=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    offering = seed_test_offering(db_session, jazz_genre=jazz_genre, owner=owner)

    create_resp = client.post(
        "/gigs",
        headers=auth_header(rider),
        json={
            "offering_id": str(offering.id),
            "note": "Checking on private_gig availability",
        },
    )
    thread_id = create_resp.json()["thread_id"]

    response = client.get(f"/threads/{thread_id}/messages", headers=auth_header(outsider))
    assert response.status_code == 403
