"""Dev-only seed data: users, acts, offerings (Appalachian NC fixtures)."""

from __future__ import annotations

import sys
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.config import settings
from app.db import SessionLocal
from app.models.act import Act
from app.models.gig_request import GigRequest, GigStatus, PaymentType
from app.models.promoter_connection import PromoterConnection, PromoterConnectionStatus
from app.models.offering import ActivityType, Offering, EquipmentProvided
from app.models.offering_availability_slot import OfferingAvailabilitySlot, SlotStatus
from app.models.oauth_account import OAuthAccount, OAuthProvider
from app.models.review import ModerationStatus, Review
from app.models.booker_experience import BookerExperienceLevel
from app.models.genre import GenreCatalog
from app.models.user import User, VerificationStatus
from app.services.flags import maybe_flag_manager_minor_skew
from app.services.public_location import default_display_location, jitter_coordinates
from app.services.security import hash_password
from app.services.slug import generate_offering_slug

DEV_PASSWORD = "password123"

# Stable UUIDs for idempotent dev references
USER_IDS = {
    "act_owner_verified": uuid.UUID("11111111-1111-4111-8111-111111111101"),
    "act_owner_verified2": uuid.UUID("11111111-1111-4111-8111-111111111102"),
    "rider_verified": uuid.UUID("11111111-1111-4111-8111-111111111103"),
    "owner_pending": uuid.UUID("11111111-1111-4111-8111-111111111104"),
    "rider_unverified": uuid.UUID("11111111-1111-4111-8111-111111111105"),
    "rider_rejected": uuid.UUID("11111111-1111-4111-8111-111111111106"),
    "oauth_only": uuid.UUID("11111111-1111-4111-8111-111111111107"),
    "guardian": uuid.UUID("11111111-1111-4111-8111-111111111108"),
    "minor_rider": uuid.UUID("11111111-1111-4111-8111-111111111109"),
    "both_verified": uuid.UUID("11111111-1111-4111-8111-111111111110"),
    "minor_rider_2": uuid.UUID("11111111-1111-4111-8111-111111111111"),
    "minor_rider_3": uuid.UUID("11111111-1111-4111-8111-111111111112"),
    "minor_rider_4": uuid.UUID("11111111-1111-4111-8111-111111111113"),
}



PLACEHOLDER_PHOTO = "https://placehold.co/600x400/e8e8e8/666?text=StageConnect"

NC_LOCATIONS = [
    ("Boone, NC 28607", 36.2168, -81.6746),
    ("Asheville, NC 28801", 35.5951, -82.5515),
    ("Blowing Rock, NC 28605", 36.1351, -81.6720),
    ("Wilkesboro, NC 28697", 36.1450, -81.2668),
    ("Hickory, NC 28601", 35.7340, -81.3442),
]

HORSE_BREEDS = [
    "Quarter Band",
    "Morgan",
    "Appaloosa",
    "Tennessee Walker",
    "Paint",
    "Arabian",
    "Thoroughbred",
    "Haflinger",
    "Mustang",
]

HORSE_NAMES = [
    "Buck",
    "Duke",
    "Clover",
    "Storm",
    "Honey",
    "Scout",
    "Blaze",
    "Pearl",
    "Ranger",
    "Sage",
    "Copper",
    "Luna",
    "Ace",
    "Ruby",
    "Finn",
    "Nova",
    "Oakley",
    "Piper",
    "Cash",
    "Ivy",
    "Colt",
    "Meadow",
    "Rocky",
    "Sierra",
    "Tucker",
    "Whisper",
    "Bandit",
    "Cinnamon",
    "Dusty",
    "Ember",
    "Fletcher",
    "Ginger",
    "Harley",
    "Jasper",
    "Koda",
]

BULK_ACTIVITY_TYPES = [
    ActivityType.WEDDING,
    ActivityType.PRIVATE_GIG,
    ActivityType.CORPORATE,
    ActivityType.FESTIVAL,
]

_BULK_MIN_SKILLS: tuple[int | None, ...] = (None, 1, 3, 4)
_BULK_WEIGHTS: tuple[int | None, ...] = (None, 180, 200, 220)
_BULK_TACK = (EquipmentProvided.PROVIDED, EquipmentProvided.BRING_OWN, EquipmentProvided.EITHER)


def _bulk_offering_community_fields(offering_idx: int) -> dict:
    return {
        "min_booker_experience": _BULK_MIN_SKILLS[offering_idx % len(_BULK_MIN_SKILLS)],
        "max_venue_capacity": _BULK_WEIGHTS[offering_idx % len(_BULK_WEIGHTS)],
        "sound_system_required": offering_idx % 7 != 0,
        "equipment_provided": _BULK_TACK[offering_idx % len(_BULK_TACK)],
    }


def _allowed() -> bool:
    return settings.seed_dev_data or settings.environment == "development"


def _name_from_email(email: str) -> tuple[str, str]:
    local = email.split("@", 1)[0]
    parts = local.replace(".", " ").replace("_", " ").split()
    if len(parts) >= 2:
        return parts[0].title(), parts[-1].title()
    return parts[0].title() if parts else "Member", ""


def upsert_user(
    db,
    *,
    user_id: uuid.UUID,
    email: str,
    is_booker: bool,
    is_act_owner: bool,
    verification_status: VerificationStatus,
    is_admin: bool = False,
    password_hash: str | None = None,
    is_minor: bool = False,
    guardian_user_id: uuid.UUID | None = None,
    created_at: datetime | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    is_act_manager: bool = False,
    is_booking_coordinator: bool = False,
    manager_verified: bool = False,
    booker_experience_level: int | None = None,
) -> User:
    derived_first, derived_last = _name_from_email(email)
    first_name = first_name or derived_first
    last_name = last_name or derived_last
    user = db.get(User, user_id)
    if user is None:
        user = db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(
            id=user_id,
            email=email,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            is_booker=is_booker,
            is_act_owner=is_act_owner,
            is_admin=is_admin,
            verification_status=verification_status,
            is_minor=is_minor,
            guardian_user_id=guardian_user_id,
            is_act_manager=is_act_manager,
            is_booking_coordinator=is_booking_coordinator,
            manager_verified=manager_verified,
            booker_experience_level=booker_experience_level,
        )
        if created_at is not None:
            user.created_at = created_at
        db.add(user)
    else:
        user.email = email
        user.password_hash = password_hash
        user.first_name = first_name
        user.last_name = last_name
        user.is_booker = is_booker
        user.is_act_owner = is_act_owner
        user.is_admin = is_admin
        user.verification_status = verification_status
        user.is_minor = is_minor
        user.guardian_user_id = guardian_user_id
        user.is_act_manager = is_act_manager
        user.is_booking_coordinator = is_booking_coordinator
        user.manager_verified = manager_verified
        user.booker_experience_level = booker_experience_level
        if created_at is not None:
            user.created_at = created_at
    return user


def _bulk_user_id(key: str) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_DNS, f"stageconnect.dev.user.bulk.{key}")


def _staggered_created_at(index: int, total: int) -> datetime:
    days_ago = max(0, 90 - (index * 90 // max(total, 1)))
    return datetime.now(UTC) - timedelta(days=days_ago)


def _rider_verification(index: int) -> VerificationStatus:
    if index % 5 < 3:
        return VerificationStatus.VERIFIED
    return [VerificationStatus.UNVERIFIED, VerificationStatus.PENDING, VerificationStatus.REJECTED][
        (index // 5) % 3
    ]


def _owner_verification(index: int) -> VerificationStatus:
    if index % 10 < 7:
        return VerificationStatus.VERIFIED
    return [VerificationStatus.UNVERIFIED, VerificationStatus.PENDING, VerificationStatus.REJECTED][
        index % 3
    ]


def _both_verification(index: int) -> VerificationStatus:
    if index % 5 < 4:
        return VerificationStatus.VERIFIED
    return VerificationStatus.PENDING if index % 2 == 0 else VerificationStatus.UNVERIFIED


def seed_bulk_users(db) -> dict[str, User]:
    hashed = hash_password(DEV_PASSWORD)
    bulk: dict[str, User] = {}
    slot = 0
    total = 50

    for n in range(1, 26):
        key = f"rider_{n:02d}"
        bulk[key] = upsert_user(
            db,
            user_id=_bulk_user_id(key),
            email=f"bulk.rider.{n:02d}@example.com",
            is_booker=True,
            is_act_owner=False,
            verification_status=_rider_verification(n),
            password_hash=hashed,
            created_at=_staggered_created_at(slot, total),
            booker_experience_level=(n % 5) + 1 if n % 5 != 0 else None,
        )
        slot += 1

    for n in range(1, 16):
        key = f"owner_{n:02d}"
        is_trainer = n % 3 == 0
        bulk[key] = upsert_user(
            db,
            user_id=_bulk_user_id(key),
            email=f"bulk.act_owner.{n:02d}@example.com",
            is_booker=False,
            is_act_owner=True,
            verification_status=_owner_verification(n),
            password_hash=hashed,
            created_at=_staggered_created_at(slot, total),
            is_act_manager=is_trainer and n % 2 == 0,
            is_booking_coordinator=is_trainer and n % 2 == 1,
        )
        slot += 1

    for n in range(1, 11):
        key = f"both_{n:02d}"
        is_trainer = n % 3 == 0
        bulk[key] = upsert_user(
            db,
            user_id=_bulk_user_id(key),
            email=f"bulk.both.{n:02d}@example.com",
            is_booker=True,
            is_act_owner=True,
            verification_status=_both_verification(n),
            password_hash=hashed,
            created_at=_staggered_created_at(slot, total),
            booker_experience_level=(n % 5) + 1 if n % 4 == 0 else None,
            is_act_manager=is_trainer and n % 2 == 0,
            is_booking_coordinator=is_trainer and n % 2 == 1,
            manager_verified=n in (2, 7),
        )
        slot += 1

    db.flush()
    return bulk


def seed_bulk_owner_assets(db, bulk: dict[str, User]) -> None:
    band_id = get_genre_id(db, "jazz")
    name_idx = 0
    acts_created: list[tuple[str, Act, User, bool]] = []

    def next_band_name() -> str:
        nonlocal name_idx
        name = HORSE_NAMES[name_idx % len(HORSE_NAMES)]
        name_idx += 1
        return name

    def add_act(owner_key: str, act_suffix: str, owner: User) -> Act:
        loc = NC_LOCATIONS[name_idx % len(NC_LOCATIONS)]
        address, lat, lng = loc
        key = f"{owner_key}-{act_suffix}"
        act = upsert_act(
            db,
            key=key,
            owner=owner,
            genre_id=band_id,
            data={
                "name": next_band_name(),
                "act_type": HORSE_BREEDS[name_idx % len(HORSE_BREEDS)],
                "years_active": 5 + (name_idx % 12),
                "description": f"Registered dev band for {act_owner.email}.",
                "lat": lat,
                "lng": lng,
                "address": address,
                "photo_urls": [PLACEHOLDER_PHOTO],
            },
        )
        return act

    for n in range(1, 9):
        owner = bulk[f"owner_{n:02d}"]
        act = add_act(f"owner-{n:02d}", "band-1", owner)
        with_offering = n > 2
        acts_created.append((f"owner-{n:02d}-band-1", act, owner, with_offering))

    for n in range(9, 16):
        owner = bulk[f"owner_{n:02d}"]
        for suffix in ("band-1", "band-2"):
            act = add_act(f"owner-{n:02d}", suffix, owner)
            with_offering = not (n == 9 and suffix == "band-2")
            acts_created.append((f"owner-{n:02d}-{suffix}", act, owner, with_offering))

    for n in range(1, 6):
        owner = bulk[f"both_{n:02d}"]
        if act_owner.verification_status != VerificationStatus.VERIFIED:
            continue
        act = add_act(f"both-{n:02d}", "band-1", owner)
        acts_created.append((f"both-{n:02d}-band-1", act, owner, True))

    offering_idx = 0
    for act_key, act, owner, with_offering in acts_created:
        if not with_offering:
            continue
        activity = BULK_ACTIVITY_TYPES[offering_idx % len(BULK_ACTIVITY_TYPES)]
        price = Decimal(str(35 + (offering_idx % 9) * 10))
        inactive = offering_idx == 3
        upsert_offering(
            db,
            key=f"bulk-{act_key}",
            owner=owner,
            act=act,
            data={
                "activity_type": activity,
                "price": price,
                "availability": "Weekends by appointment",
                "promoter_only_allowed": False,
                "active": not inactive,
                **_bulk_offering_community_fields(offering_idx),
            },
        )
        offering_idx += 1


def seed_users(db) -> dict[str, User]:
    hashed = hash_password(DEV_PASSWORD)
    users = {
        "act_owner_verified": upsert_user(
            db,
            user_id=USER_IDS["act_owner_verified"],
            email="act_owner.verified@example.com",
            is_booker=False,
            is_act_owner=True,
            verification_status=VerificationStatus.VERIFIED,
            password_hash=hashed,
            is_booking_coordinator=True,
        ),
        "act_owner_verified2": upsert_user(
            db,
            user_id=USER_IDS["act_owner_verified2"],
            email="act_owner.verified2@example.com",
            is_booker=False,
            is_act_owner=True,
            verification_status=VerificationStatus.VERIFIED,
            password_hash=hashed,
            is_act_manager=True,
            is_booking_coordinator=True,
            manager_verified=True,
        ),
        "rider_verified": upsert_user(
            db,
            user_id=USER_IDS["rider_verified"],
            email="rider.verified@example.com",
            is_booker=True,
            is_act_owner=False,
            verification_status=VerificationStatus.VERIFIED,
            password_hash=hashed,
            booker_experience_level=BookerExperienceLevel.BEGINNER.value,
        ),
        "owner_pending": upsert_user(
            db,
            user_id=USER_IDS["owner_pending"],
            email="act_owner.pending@example.com",
            is_booker=False,
            is_act_owner=True,
            verification_status=VerificationStatus.PENDING,
            password_hash=hashed,
        ),
        "rider_unverified": upsert_user(
            db,
            user_id=USER_IDS["rider_unverified"],
            email="rider.unverified@example.com",
            is_booker=True,
            is_act_owner=False,
            verification_status=VerificationStatus.UNVERIFIED,
            password_hash=hashed,
        ),
        "rider_rejected": upsert_user(
            db,
            user_id=USER_IDS["rider_rejected"],
            email="rider.rejected@example.com",
            is_booker=True,
            is_act_owner=False,
            verification_status=VerificationStatus.REJECTED,
            password_hash=hashed,
        ),
        "guardian": upsert_user(
            db,
            user_id=USER_IDS["guardian"],
            email="guardian@example.com",
            is_booker=True,
            is_act_owner=True,
            verification_status=VerificationStatus.VERIFIED,
            password_hash=hashed,
        ),
        "minor_rider": upsert_user(
            db,
            user_id=USER_IDS["minor_rider"],
            email="minor.rider@example.com",
            is_booker=True,
            is_act_owner=False,
            verification_status=VerificationStatus.UNVERIFIED,
            password_hash=hashed,
            is_minor=True,
            guardian_user_id=USER_IDS["guardian"],
        ),
        "oauth_only": upsert_user(
            db,
            user_id=USER_IDS["oauth_only"],
            email="oauth.only@example.com",
            is_booker=False,
            is_act_owner=False,
            verification_status=VerificationStatus.UNVERIFIED,
            password_hash=None,
        ),
        "both_verified": upsert_user(
            db,
            user_id=USER_IDS["both_verified"],
            email="both.verified@example.com",
            is_booker=True,
            is_act_owner=True,
            verification_status=VerificationStatus.VERIFIED,
            password_hash=hashed,
            booker_experience_level=BookerExperienceLevel.INTERMEDIATE.value,
        ),
        "minor_rider_2": upsert_user(
            db,
            user_id=USER_IDS["minor_rider_2"],
            email="minor.rider2@example.com",
            is_booker=True,
            is_act_owner=False,
            verification_status=VerificationStatus.VERIFIED,
            password_hash=hashed,
            is_minor=True,
            guardian_user_id=USER_IDS["guardian"],
            first_name="Casey",
            last_name="Minor",
        ),
        "minor_rider_3": upsert_user(
            db,
            user_id=USER_IDS["minor_rider_3"],
            email="minor.rider3@example.com",
            is_booker=True,
            is_act_owner=False,
            verification_status=VerificationStatus.VERIFIED,
            password_hash=hashed,
            is_minor=True,
            guardian_user_id=USER_IDS["guardian"],
            first_name="Jordan",
            last_name="Minor",
        ),
        "minor_rider_4": upsert_user(
            db,
            user_id=USER_IDS["minor_rider_4"],
            email="minor.rider4@example.com",
            is_booker=True,
            is_act_owner=False,
            verification_status=VerificationStatus.VERIFIED,
            password_hash=hashed,
            is_minor=True,
            guardian_user_id=USER_IDS["guardian"],
            first_name="Taylor",
            last_name="Minor",
        ),
    }
    db.flush()

    oauth_user = users["oauth_only"]
    oauth = db.scalar(
        select(OAuthAccount).where(
            OAuthAccount.provider == OAuthProvider.GOOGLE,
            OAuthAccount.provider_user_id == "google-dev-oauth-only",
        )
    )
    if oauth is None:
        db.add(
            OAuthAccount(
                user_id=oauth_user.id,
                provider=OAuthProvider.GOOGLE,
                provider_user_id="google-dev-oauth-only",
                provider_email=oauth_user.email,
                provider_email_verified=True,
            )
        )
    return users


def get_genre_id(db, name: str) -> uuid.UUID:
    genres = db.scalar(select(GenreCatalog).where(GenreCatalog.name == name))
    if genres is None:
        raise RuntimeError(f"GenreCatalog '{name}' not found — run migrations first")
    return genres.id


def upsert_act(db, *, key: str, owner: User, genre_id: uuid.UUID, data: dict) -> Act:
    act_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"stageconnect.dev.act.{key}")
    act = db.get(Act, act_id)
    if act is None:
        act = Act(id=act_id, act_owner_id=act_owner.id, genre_id=genre_id, **data)
        db.add(act)
    else:
        for field, value in data.items():
            setattr(act, field, value)
        act.act_owner_id = act_owner.id
        act.genre_id = genre_id
    return act


def upsert_offering(db, *, key: str, owner: User, act: Act, data: dict) -> Offering:
    offering_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"stageconnect.dev.offering.{key}")
    offering = db.get(Offering, offering_id)
    display_location = data.pop("display_location", None) or default_display_location(act.address)
    if offering is None:
        slug = generate_offering_slug(act.name)
        public_lat, public_lng = jitter_coordinates(
            act.id, act.lat, act.lng, settings.service_area_default_secret
        )
        offering = Offering(
            id=offering_id,
            act_id=act.id,
            act_owner_id=act_owner.id,
            slug=slug,
            display_location=display_location,
            public_lat=public_lat,
            public_lng=public_lng,
            **data,
        )
        db.add(offering)
    else:
        offering.act_id = act.id
        offering.act_owner_id = act_owner.id
        if not offering.slug:
            offering.slug = generate_offering_slug(act.name)
        if offering.public_lat is None or offering.public_lng is None:
            offering.public_lat, offering.public_lng = jitter_coordinates(
                act.id, act.lat, act.lng, settings.service_area_default_secret
            )
        offering.display_location = display_location
        for field, value in data.items():
            setattr(offering, field, value)
    return offering


def seed_acts_and_offerings(db, users: dict[str, User]) -> None:
    band_id = get_genre_id(db, "jazz")
    owner1 = users["act_owner_verified"]
    owner2 = users["act_owner_verified2"]

    acts_data = [
        (
            "star",
            owner1,
            {
                "name": "Star",
                "act_type": "Quarter Band",
                "years_active": 8,
                "description": "Calm trail band, great for beginners on mountain paths.",
                "lat": 36.2168,
                "lng": -81.6746,
                "address": "742 Mountain Rd, Boone, NC 28607",
                "photo_urls": [PLACEHOLDER_PHOTO],
                "genres": ["jazz"],
            },
        ),
        (
            "misty",
            owner1,
            {
                "name": "Misty",
                "act_type": "Tennessee Walker",
                "years_active": 12,
                "description": "Smooth-gaited mare for scenic Blue Ridge rides.",
                "lat": 35.5951,
                "lng": -82.5515,
                "address": "Asheville, NC 28801",
                "photo_urls": [PLACEHOLDER_PHOTO],
                "genres": ["rock"],
            },
        ),
        (
            "rusty",
            owner1,
            {
                "name": "Rusty",
                "act_type": "Paint",
                "years_active": 6,
                "description": "Energetic gelding suited for intermediate riders.",
                "lat": 36.1351,
                "lng": -81.6720,
                "address": "Blowing Rock, NC 28605",
                "photo_urls": [PLACEHOLDER_PHOTO],
                "genres": ["jazz", "rock"],
            },
        ),
        (
            "daisy",
            owner2,
            {
                "name": "Daisy",
                "act_type": "Appaloosa",
                "years_active": 10,
                "description": "Lesson band with years of arena experience.",
                "lat": 36.2185,
                "lng": -81.6812,
                "address": "Boone, NC 28607",
                "photo_urls": [PLACEHOLDER_PHOTO],
                "genres": ["rock"],
            },
        ),
        (
            "comet",
            owner2,
            {
                "name": "Comet",
                "act_type": "Arabian",
                "years_active": 7,
                "description": "Day rental available for experienced riders.",
                "lat": 35.6009,
                "lng": -82.5540,
                "address": "88 Riverside Dr, Asheville, NC 28801",
                "photo_urls": [PLACEHOLDER_PHOTO],
                "genres": ["jazz"],
            },
        ),
        (
            "willow",
            owner2,
            {
                "name": "Willow",
                "act_type": "Morgan",
                "years_active": 9,
                "description": "Gentle private_gig band for children and adults.",
                "lat": 36.1450,
                "lng": -81.2668,
                "address": "Wilkesboro, NC 28697",
                "photo_urls": [PLACEHOLDER_PHOTO],
                "genres": ["therapy"],
            },
        ),
        (
            "shadow",
            owner2,
            {
                "name": "Shadow",
                "act_type": "Thoroughbred",
                "years_active": 5,
                "description": "Athletic gelding for corporate arrangements.",
                "lat": 35.7340,
                "lng": -81.3442,
                "address": "Hickory, NC 28601",
                "photo_urls": [PLACEHOLDER_PHOTO],
                "genres": ["rock"],
            },
        ),
        (
            "maple",
            users["both_verified"],
            {
                "name": "Maple",
                "act_type": "Haflinger",
                "years_active": 11,
                "description": "Family-friendly trail band on a small ranch.",
                "lat": 36.2100,
                "lng": -81.6800,
                "address": "Boone, NC 28607",
                "photo_urls": [PLACEHOLDER_PHOTO],
                "genres": ["jazz", "rock"],
            },
        ),
        (
            "river",
            users["both_verified"],
            {
                "name": "River",
                "act_type": "Mustang",
                "years_active": 8,
                "description": "Trail rides along the New River corridor.",
                "lat": 36.1400,
                "lng": -81.6700,
                "address": "Blowing Rock, NC 28605",
                "photo_urls": [PLACEHOLDER_PHOTO],
                "genres": ["jazz"],
            },
        ),
    ]

    acts: dict[str, Act] = {}
    for key, owner, data in acts_data:
        acts[key] = upsert_act(db, key=key, owner=owner, genre_id=band_id, data=data)

    offerings_data = [
        (
            "star-trail",
            acts["star"],
            owner1,
            {
                "activity_type": ActivityType.WEDDING,
                "price": Decimal("75.00"),
                "availability": "Saturday and Sunday mornings",
                "promoter_only_allowed": False,
                "active": True,
            },
        ),
        (
            "misty-trail",
            acts["misty"],
            owner1,
            {
                "activity_type": ActivityType.WEDDING,
                "price": Decimal("85.00"),
                "availability": "Weekends by appointment",
                "promoter_only_allowed": False,
                "active": True,
            },
        ),
        (
            "rusty-private_gig",
            acts["rusty"],
            owner1,
            {
                "activity_type": ActivityType.PRIVATE_GIG,
                "price": Decimal("60.00"),
                "availability": "Tuesday and Thursday afternoons",
                "promoter_only_allowed": False,
                "active": True,
            },
        ),
        (
            "daisy-private_gig",
            acts["daisy"],
            owner2,
            {
                "activity_type": ActivityType.PRIVATE_GIG,
                "price": Decimal("55.00"),
                "availability": "Weekday mornings",
                "promoter_only_allowed": False,
                "active": True,
            },
        ),
        (
            "comet-rental",
            acts["comet"],
            owner2,
            {
                "activity_type": ActivityType.FESTIVAL,
                "price": Decimal("120.00"),
                "availability": "Advance booking required",
                "promoter_only_allowed": False,
                "active": True,
            },
        ),
        (
            "star-friend",
            acts["star"],
            owner1,
            {
                "activity_type": ActivityType.WEDDING,
                "price": Decimal("0.00"),
                "availability": "Verified friends only — contact via platform",
                "promoter_only_allowed": True,
                "active": True,
            },
        ),
        (
            "misty-inactive",
            acts["misty"],
            owner1,
            {
                "activity_type": ActivityType.CORPORATE,
                "price": Decimal("300.00"),
                "availability": "Monthly corporate — currently paused",
                "promoter_only_allowed": False,
                "active": False,
            },
        ),
        (
            "willow-private_gig",
            acts["willow"],
            owner2,
            {
                "activity_type": ActivityType.PRIVATE_GIG,
                "price": Decimal("45.00"),
                "availability": "After-school slots",
                "promoter_only_allowed": False,
                "active": True,
            },
        ),
        (
            "shadow-corporate",
            acts["shadow"],
            owner2,
            {
                "activity_type": ActivityType.CORPORATE,
                "price": Decimal("150.00"),
                "availability": "Monthly partial corporate",
                "promoter_only_allowed": False,
                "active": True,
            },
        ),
        (
            "daisy-trail",
            acts["daisy"],
            owner2,
            {
                "activity_type": ActivityType.WEDDING,
                "price": Decimal("65.00"),
                "availability": "Weekend mornings",
                "promoter_only_allowed": False,
                "active": True,
            },
        ),
        (
            "comet-day",
            acts["comet"],
            owner2,
            {
                "activity_type": ActivityType.FESTIVAL,
                "price": Decimal("110.00"),
                "availability": "Full day, rider supplies tack",
                "promoter_only_allowed": False,
                "active": True,
            },
        ),
        (
            "rusty-friend",
            acts["rusty"],
            owner1,
            {
                "activity_type": ActivityType.WEDDING,
                "price": Decimal("0.00"),
                "availability": "Verified friends only",
                "promoter_only_allowed": True,
                "active": True,
            },
        ),
        (
            "maple-trail",
            acts["maple"],
            users["both_verified"],
            {
                "activity_type": ActivityType.WEDDING,
                "price": Decimal("55.00"),
                "availability": "Saturday afternoons",
                "promoter_only_allowed": False,
                "active": True,
            },
        ),
        (
            "maple-private_gig",
            acts["maple"],
            users["both_verified"],
            {
                "activity_type": ActivityType.PRIVATE_GIG,
                "price": Decimal("40.00"),
                "availability": "Weekday evenings",
                "promoter_only_allowed": False,
                "active": True,
            },
        ),
        (
            "river-trail",
            acts["river"],
            users["both_verified"],
            {
                "activity_type": ActivityType.WEDDING,
                "price": Decimal("70.00"),
                "availability": "Sunday group rides",
                "promoter_only_allowed": False,
                "active": True,
            },
        ),
        (
            "river-friend",
            acts["river"],
            users["both_verified"],
            {
                "activity_type": ActivityType.WEDDING,
                "price": Decimal("0.00"),
                "availability": "Friends and family only",
                "promoter_only_allowed": True,
                "active": True,
            },
        ),
        (
            "star-private_gig",
            acts["star"],
            owner1,
            {
                "activity_type": ActivityType.PRIVATE_GIG,
                "price": Decimal("50.00"),
                "availability": "Beginner private_gigs — weekday mornings",
                "promoter_only_allowed": False,
                "active": True,
            },
        ),
        (
            "misty-corporate",
            acts["misty"],
            owner1,
            {
                "activity_type": ActivityType.CORPORATE,
                "price": Decimal("250.00"),
                "availability": "Monthly corporate — 3 rides per week",
                "promoter_only_allowed": False,
                "active": True,
            },
        ),
    ]

    _CURATED_LISTING_COMMUNITY: dict[str, dict] = {
        "star-trail": {
            "min_booker_experience": BookerExperienceLevel.BEGINNER.value,
            "sound_system_required": True,
            "equipment_provided": EquipmentProvided.PROVIDED,
        },
        "star-private_gig": {
            "min_booker_experience": BookerExperienceLevel.BEGINNER.value,
            "max_venue_capacity": 200,
            "sound_system_required": True,
            "equipment_provided": EquipmentProvided.PROVIDED,
        },
        "willow-private_gig": {
            "min_booker_experience": BookerExperienceLevel.BEGINNER.value,
            "max_venue_capacity": 220,
            "sound_system_required": True,
            "equipment_provided": EquipmentProvided.PROVIDED,
        },
        "rusty-private_gig": {
            "min_booker_experience": BookerExperienceLevel.INTERMEDIATE.value,
            "sound_system_required": True,
            "equipment_provided": EquipmentProvided.EITHER,
        },
        "daisy-private_gig": {
            "min_booker_experience": BookerExperienceLevel.INTERMEDIATE.value,
            "sound_system_required": True,
            "equipment_provided": EquipmentProvided.EITHER,
        },
        "comet-rental": {
            "min_booker_experience": BookerExperienceLevel.ADVANCED_INTERMEDIATE.value,
            "max_venue_capacity": 180,
            "sound_system_required": True,
            "equipment_provided": EquipmentProvided.BRING_OWN,
        },
        "shadow-corporate": {
            "min_booker_experience": BookerExperienceLevel.ADVANCED_INTERMEDIATE.value,
            "max_venue_capacity": 175,
            "sound_system_required": True,
            "equipment_provided": EquipmentProvided.BRING_OWN,
        },
        "star-friend": {"min_booker_experience": BookerExperienceLevel.BEGINNER.value},
        "rusty-friend": {"min_booker_experience": BookerExperienceLevel.BEGINNER.value},
        "river-friend": {"min_booker_experience": BookerExperienceLevel.BEGINNER.value},
    }

    for key, act, owner, data in offerings_data:
        merged = {**data, **_CURATED_LISTING_COMMUNITY.get(key, {})}
        upsert_offering(db, key=key, owner=owner, act=act, data=merged)


def upsert_availability_slot(
    db,
    *,
    key: str,
    offering: Offering,
    start_at: datetime,
    end_at: datetime,
    status: SlotStatus = SlotStatus.OPEN,
) -> OfferingAvailabilitySlot:
    slot_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"stageconnect.dev.slot.{key}")
    slot = db.get(OfferingAvailabilitySlot, slot_id)
    if slot is None:
        slot = OfferingAvailabilitySlot(
            id=slot_id,
            offering_id=offering.id,
            start_at=start_at,
            end_at=end_at,
            status=status,
        )
        db.add(slot)
    else:
        slot.offering_id = offering.id
        slot.start_at = start_at
        slot.end_at = end_at
        slot.status = status
    return slot


def seed_availability_slots(db) -> None:
    """Open slots on a few active offerings for calendar discovery in dev."""
    offering_keys = ("star-trail", "misty-trail", "rusty-private_gig")
    base = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    for offering_index, offering_key in enumerate(offering_keys):
        offering_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"stageconnect.dev.offering.{offering_key}")
        offering = db.get(Offering, offering_id)
        if offering is None or not offering.active:
            continue
        for day_offset in (2, 5, 9, 13):
            start_at = base + timedelta(days=day_offset, hours=10 + offering_index)
            end_at = start_at + timedelta(hours=2)
            upsert_availability_slot(
                db,
                key=f"{offering_key}-d{day_offset}",
                offering=offering,
                start_at=start_at,
                end_at=end_at,
            )


def upsert_promoter_connection(
    db,
    *,
    key: str,
    owner: User,
    rider: User | None,
    email: str,
    status: PromoterConnectionStatus,
    created_at: datetime | None = None,
) -> PromoterConnection:
    invite_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"stageconnect.dev.friend.{key}")
    invite = db.get(PromoterConnection, invite_id)
    if invite is None:
        invite = PromoterConnection(
            id=invite_id,
            act_owner_id=act_owner.id,
            booker_id=rider.id if rider else None,
            invitee_email=email.lower(),
            status=status,
        )
        if created_at is not None:
            invite.created_at = created_at
            invite.invited_at = created_at
        db.add(invite)
    else:
        invite.act_owner_id = act_owner.id
        invite.booker_id = rider.id if rider else None
        invite.invitee_email = email.lower()
        invite.status = status
        if created_at is not None:
            invite.created_at = created_at
            invite.invited_at = created_at
    return invite


def seed_promoter_connections(db, users: dict[str, User], bulk: dict[str, User]) -> None:
    owner = users["act_owner_verified"]
    trainer_owner = users["act_owner_verified2"]
    rider = users["rider_verified"]
    recent = datetime.now(UTC) - timedelta(days=14)

    upsert_promoter_connection(
        db,
        key="owner-rider-accepted",
        owner=owner,
        rider=rider,
        email=rider.email,
        status=PromoterConnectionStatus.ACTIVE,
    )
    upsert_promoter_connection(
        db,
        key="owner-unverified-pending",
        owner=owner,
        rider=users["rider_unverified"],
        email=users["rider_unverified"].email,
        status=PromoterConnectionStatus.PENDING_ACT_OWNER_CONFIRM,
    )

    for idx, minor_key in enumerate(("minor_rider_2", "minor_rider_3", "minor_rider_4"), start=1):
        minor = users[minor_key]
        upsert_promoter_connection(
            db,
            key=f"trainer-minor-{idx}",
            owner=trainer_owner,
            rider=minor,
            email=minor.email,
            status=PromoterConnectionStatus.ACTIVE,
            created_at=recent - timedelta(days=idx),
        )

    for idx, bulk_key in enumerate(("rider_01", "rider_02"), start=1):
        adult = bulk[bulk_key]
        upsert_promoter_connection(
            db,
            key=f"trainer-adult-{idx}",
            owner=trainer_owner,
            rider=adult,
            email=adult.email,
            status=PromoterConnectionStatus.ACTIVE,
            created_at=recent - timedelta(days=idx + 3),
        )

    maybe_flag_manager_minor_skew(db, trainer_act_owner.id)


def upsert_booking(db, *, key: str, offering: Offering, rider: User, status: GigStatus, payment_type: PaymentType, note: str | None = None) -> GigRequest:
    booking_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"stageconnect.dev.booking.{key}")
    booking = db.get(GigRequest, booking_id)
    if booking is None:
        booking = GigRequest(
            id=booking_id,
            offering_id=offering.id,
            booker_id=rider.id,
            act_owner_id=offering.act_owner_id,
            payment_type=payment_type,
            status=status,
            note=note,
        )
        db.add(booking)
    else:
        booking.offering_id = offering.id
        booking.booker_id = rider.id
        booking.act_owner_id = offering.act_owner_id
        booking.payment_type = payment_type
        booking.status = status
        booking.note = note
    return booking


def seed_gig_requests(db, users: dict[str, User]) -> None:
    star_trail_id = uuid.uuid5(uuid.NAMESPACE_DNS, "stageconnect.dev.offering.star-trail")
    rusty_private_gig_id = uuid.uuid5(uuid.NAMESPACE_DNS, "stageconnect.dev.offering.rusty-private_gig")
    comet_rental_id = uuid.uuid5(uuid.NAMESPACE_DNS, "stageconnect.dev.offering.comet-rental")
    daisy_trail_id = uuid.uuid5(uuid.NAMESPACE_DNS, "stageconnect.dev.offering.daisy-trail")
    star_trail = db.get(Offering, star_trail_id)
    rusty_private_gig = db.get(Offering, rusty_private_gig_id)
    comet_rental = db.get(Offering, comet_rental_id)
    daisy_trail = db.get(Offering, daisy_trail_id)
    if star_trail is None or rusty_private_gig is None:
        return
    rider = users["rider_verified"]
    upsert_booking(
        db,
        key="pending-paid",
        offering=star_trail,
        rider=rider,
        status=GigStatus.PENDING_PAYMENT,
        payment_type=PaymentType.PAID,
        note="Hope to ride Saturday morning",
    )
    upsert_booking(
        db,
        key="approved-paid",
        offering=rusty_private_gig,
        rider=rider,
        status=GigStatus.APPROVED,
        payment_type=PaymentType.PAID,
    )
    upsert_booking(
        db,
        key="declined-paid",
        offering=star_trail,
        rider=users["both_verified"],
        status=GigStatus.DECLINED,
        payment_type=PaymentType.PAID,
        note="Schedule conflict",
    )
    if comet_rental is not None:
        upsert_booking(
            db,
            key="skill-mismatch-pending",
            offering=comet_rental,
            rider=rider,
            status=GigStatus.PENDING_ACT_OWNER,
            payment_type=PaymentType.PAID,
            note="Interested in a full-day rental",
        )
    if daisy_trail is not None:
        upsert_booking(
            db,
            key="completed-daisy-trail",
            offering=daisy_trail,
            rider=users["both_verified"],
            status=GigStatus.COMPLETED,
            payment_type=PaymentType.PAID,
        )
        upsert_booking(
            db,
            key="completed-rusty-private_gig",
            offering=rusty_private_gig,
            rider=users["both_verified"],
            status=GigStatus.COMPLETED,
            payment_type=PaymentType.PAID,
        )





def upsert_review(
    db,
    *,
    key: str,
    booking: GigRequest,
    reviewer: User,
    reviewee: User,
    rating: int,
    observed_booker_experience: int | None = None,
    body: str | None = None,
    published_at: datetime | None = None,
) -> Review:
    review_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"stageconnect.dev.review.{key}")
    review = db.get(Review, review_id)
    if review is None:
        review = Review(
            id=review_id,
            gig_request_id=booking.id,
            reviewer_id=reviewer.id,
            reviewee_id=reviewee.id,
            rating=rating,
            body=body,
            observed_booker_experience=observed_booker_experience,
            moderation_status=ModerationStatus.APPROVED,
            published_at=published_at or datetime.now(UTC),
        )
        db.add(review)
    else:
        review.gig_request_id = booking.id
        review.reviewer_id = reviewer.id
        review.reviewee_id = reviewee.id
        review.rating = rating
        review.body = body
        review.observed_booker_experience = observed_booker_experience
        review.moderation_status = ModerationStatus.APPROVED
        review.published_at = published_at or datetime.now(UTC)
    return review


def seed_reviews(db, users: dict[str, User]) -> None:
    daisy_booking_id = uuid.uuid5(uuid.NAMESPACE_DNS, "stageconnect.dev.booking.completed-daisy-trail")
    rusty_booking_id = uuid.uuid5(uuid.NAMESPACE_DNS, "stageconnect.dev.booking.completed-rusty-private_gig")
    daisy_booking = db.get(GigRequest, daisy_booking_id)
    rusty_booking = db.get(GigRequest, rusty_booking_id)
    if daisy_booking is None or rusty_booking is None:
        return
    rider = users["both_verified"]
    published = datetime.now(UTC) - timedelta(days=7)
    upsert_review(
        db,
        key="owner2-observed-both",
        booking=daisy_booking,
        reviewer=users["act_owner_verified2"],
        reviewee=rider,
        rating=5,
        observed_booker_experience=BookerExperienceLevel.INTERMEDIATE.value,
        body="Solid intermediate rider on the trail.",
        published_at=published,
    )
    upsert_review(
        db,
        key="owner1-observed-both",
        booking=rusty_booking,
        reviewer=users["act_owner_verified"],
        reviewee=rider,
        rating=4,
        observed_booker_experience=BookerExperienceLevel.INTERMEDIATE.value,
        body="Handled the private_gig band confidently.",
        published_at=published,
    )


def run_seed() -> None:
    if not _allowed():
        print("Refusing to seed: set SEED_DEV_DATA=true or ENVIRONMENT=development")
        sys.exit(1)

    db = SessionLocal()
    try:
        users = seed_users(db)
        bulk = seed_bulk_users(db)
        seed_acts_and_offerings(db, users)
        seed_availability_slots(db)
        seed_bulk_owner_assets(db, bulk)
        seed_promoter_connections(db, users, bulk)
        seed_gig_requests(db, users)
        seed_reviews(db, users)
        db.commit()
        print("Dev seed complete.")
        print(f"Dev password for email users: {DEV_PASSWORD}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
