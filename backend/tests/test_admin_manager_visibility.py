from app.models.user import VerificationStatus
from tests.conftest import auth_header, create_user


def test_admin_stats_and_user_list_include_trainer_counts(
    client, db_session
) -> None:
    admin_user = create_user(
        db_session,
        email="admin-trainer@example.com",
        is_admin=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    create_user(
        db_session,
        email="trainer-persona@example.com",
        is_act_owner=True,
        is_booker=False,
        is_act_manager=True,
        is_booking_coordinator=True,
        manager_verified=True,
        verification_status=VerificationStatus.VERIFIED,
    )

    stats_response = client.get("/admin/stats", headers=auth_header(admin_user))
    assert stats_response.status_code == 200
    stats = stats_response.json()

    users_response = client.get("/admin/users", headers=auth_header(admin_user))
    assert users_response.status_code == 200
    trainer_row = next(
        item
        for item in users_response.json()["items"]
        if item["email"] == "trainer-persona@example.com"
    )

    assert trainer_row["is_act_manager"] is True
    assert trainer_row["is_booking_coordinator"] is True
    assert trainer_row["manager_verified"] is True
    assert trainer_row["is_act_owner"] is True
    assert trainer_row["is_booker"] is False
    assert stats["manager_users"] >= 1
    assert stats["verified_manager_users"] >= 1
