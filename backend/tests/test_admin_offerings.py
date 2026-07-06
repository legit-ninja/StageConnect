from decimal import Decimal

from sqlalchemy import select

from app.models.admin_audit_log import AdminAuditAction, AdminAuditLog
from app.models.user import VerificationStatus
from tests.helpers import seed_test_offering


def test_admin_deactivate_offering_writes_audit(
    client, db_session, jazz_genre
) -> None:
    from tests.conftest import auth_header, create_user

    admin = create_user(
        db_session,
        email="admin@example.com",
        is_admin=True,
        is_act_owner=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    owner = create_user(
        db_session,
        email="owner@example.com",
        is_act_owner=True,
        verification_status=VerificationStatus.VERIFIED,
    )
    offering = seed_test_offering(
        db_session,
        jazz_genre=jazz_genre,
        owner=owner,
        price=Decimal("75.00"),
        active=True,
    )

    response = client.patch(
        f"/admin/offerings/{offering.id}",
        headers=auth_header(admin),
        json={"active": False},
    )
    assert response.status_code == 200
    assert response.json()["active"] is False

    audit = db_session.scalar(select(AdminAuditLog))
    assert audit is not None
    assert audit.action == AdminAuditAction.OFFERING_DEACTIVATED


def test_non_admin_cannot_list_admin_offerings(
    client, db_session
) -> None:
    from tests.conftest import auth_header, create_user

    user = create_user(db_session, email="user@example.com")
    response = client.get("/admin/offerings", headers=auth_header(user))
    assert response.status_code == 403
