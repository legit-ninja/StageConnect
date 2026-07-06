import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.models.genre import GenreCatalog
from app.models.user import User, VerificationStatus
from app.services.security import create_access_token, hash_password


@pytest.fixture(autouse=True)
def _test_jitter_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SERVICE_AREA_DEFAULT_SECRET", "test-jitter-secret")
    from app.config import settings

    settings.service_area_default_secret = "test-jitter-secret"


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def jazz_genre(db_session: Session) -> GenreCatalog:
    genre = GenreCatalog(name="jazz", active_in_ui=True)
    db_session.add(genre)
    db_session.commit()
    db_session.refresh(genre)
    return genre


def create_user(
    db: Session,
    *,
    email: str,
    is_admin: bool = False,
    is_act_owner: bool = False,
    is_act_manager: bool = False,
    is_booking_coordinator: bool = False,
    manager_verified: bool = False,
    booker_experience_level: int | None = None,
    is_booker: bool = True,
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED,
    is_minor: bool = False,
) -> User:
    user = User(
        email=email,
        password_hash=hash_password("password123"),
        first_name="Test",
        last_name="User",
        is_booker=is_booker,
        is_act_owner=is_act_owner,
        is_act_manager=is_act_manager,
        is_booking_coordinator=is_booking_coordinator,
        manager_verified=manager_verified,
        booker_experience_level=booker_experience_level,
        is_admin=is_admin,
        verification_status=verification_status,
        is_minor=is_minor,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def auth_header(user: User) -> dict[str, str]:
    token = create_access_token(user.id, user.email, user.is_admin)
    return {"Authorization": f"Bearer {token}"}
