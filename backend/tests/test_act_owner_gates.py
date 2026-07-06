from app.models.user import VerificationStatus


def test_unverified_owner_cannot_create_act(
    client, db_session, jazz_genre
) -> None:
    from tests.conftest import auth_header, create_user

    owner = create_user(
        db_session,
        email="pending@example.com",
        is_act_owner=True,
        verification_status=VerificationStatus.PENDING,
    )
    response = client.post(
        "/act-owner/acts",
        headers=auth_header(owner),
        json={
            "genre_id": str(jazz_genre.id),
            "name": "New Band",
            "lat": 36.2,
            "lng": -81.6,
            "address": "Boone, NC",
            "photo_urls": [],
            "genres": ["jazz"],
        },
    )
    assert response.status_code == 403


def test_verified_owner_can_create_act(
    client, db_session, jazz_genre
) -> None:
    from tests.conftest import auth_header, create_user

    owner = create_user(
        db_session,
        email="verified@example.com",
        is_act_owner=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    response = client.post(
        "/act-owner/acts",
        headers=auth_header(owner),
        json={
            "genre_id": str(jazz_genre.id),
            "name": "New Band",
            "lat": 36.2,
            "lng": -81.6,
            "address": "Boone, NC",
            "photo_urls": [],
            "genres": ["jazz"],
        },
    )
    assert response.status_code == 201
    assert response.json()["name"] == "New Band"
