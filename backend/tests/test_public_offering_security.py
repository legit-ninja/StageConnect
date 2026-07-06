import json

from app.models.user import VerificationStatus
from tests.helpers import seed_test_offering

FORBIDDEN_KEYS = {
    "address",
    "lat",
    "lng",
    "description",
    "act_owner_id",
    "act_id",
    "act_owner_email",
    "owner_last_name",
    "email",
    "phone",
}


def test_public_offering_does_not_leak_private_fields(
    client, db_session, jazz_genre
) -> None:
    from tests.conftest import create_user

    owner = create_user(
        db_session,
        email="secret.owner@example.com",
        is_act_owner=True,
        verification_status=VerificationStatus.VERIFIED,
        is_booker=False,
    )
    owner.last_name = "Secretlastname"
    db_session.commit()

    offering = seed_test_offering(
        db_session,
        jazz_genre=jazz_genre,
        owner=owner,
        act_name="Midnight",
        address="123 Hidden Farm Rd, Boone, NC 28607",
        lat=36.2168,
        lng=-81.6746,
    )
    act = offering.act
    act.description = "Private barn notes with gate code"
    db_session.commit()

    response = client.get(f"/public/offerings/{offering.slug}")
    assert response.status_code == 200
    payload = response.json()
    serialized = json.dumps(payload).lower()

    for key in FORBIDDEN_KEYS:
        assert key not in payload, f"forbidden key leaked: {key}"

    assert "123 hidden farm" not in serialized
    assert "secret.owner@example.com" not in serialized
    assert "secretlastname" not in serialized
    assert payload["act_owner_first_name"] == "Test"
    assert payload["act_owner_last_initial"] == "S"
    assert payload["display_location"] != act.address
    assert payload["public_lat"] != act.lat or payload["public_lng"] != act.lng
    assert payload["genres"] == ["jazz"]
    assert "min_booker_experience" in payload
    assert "booker_experience_level" not in payload
