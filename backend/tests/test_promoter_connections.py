from app.models.user import User, VerificationStatus
from app.services.security import create_access_token, hash_password


def test_non_owner_cannot_create_promoter_connection(client, db_session) -> None:
    from tests.conftest import auth_header, create_user

    rider = create_user(
        db_session,
        email="rider-fi@example.com",
        is_booker=True,
        is_act_owner=False,
        verification_status=VerificationStatus.VERIFIED,
    )
    response = client.post(
        "/act-owner/promoter-connections",
        headers=auth_header(rider),
        json={"invitee_email": "target@example.com"},
    )
    assert response.status_code == 403


def test_owner_creates_promoter_connection(client, db_session) -> None:
    from tests.conftest import auth_header, create_user

    owner = create_user(
        db_session,
        email="owner-fi@example.com",
        is_act_owner=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    create_user(
        db_session,
        email="target@example.com",
        is_booker=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    response = client.post(
        "/act-owner/promoter-connections",
        headers=auth_header(owner),
        json={"invitee_email": "target@example.com"},
    )
    assert response.status_code == 201
    assert response.json()["status"] == "pending_act_owner_confirm"


def test_rider_accepts_promoter_connection(client, db_session) -> None:
    from tests.conftest import auth_header, create_user

    owner = create_user(
        db_session,
        email="owner-fi2@example.com",
        is_act_owner=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    rider = create_user(
        db_session,
        email="rider-fi2@example.com",
        is_booker=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    create_resp = client.post(
        "/act-owner/promoter-connections",
        headers=auth_header(owner),
        json={"invitee_email": rider.email},
    )
    invite_id = create_resp.json()["id"]
    response = client.patch(
        f"/booker/promoter-connections/{invite_id}/respond",
        headers=auth_header(rider),
        json={"status": "accepted"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "active"
