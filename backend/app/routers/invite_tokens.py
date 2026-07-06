import secrets
import uuid
from datetime import UTC, datetime, timedelta
from io import BytesIO

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from PIL import Image
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.config import settings
from app.db import get_db
from app.dependencies import require_act_owner, require_verified
from app.models.act import Act
from app.models.promoter_connection import PromoterConnection, PromoterConnectionStatus
from app.models.invite_token import InviteToken
from app.models.offering import Offering
from app.models.offering_photo import OfferingPhoto
from app.models.review import ModerationStatus
from app.models.user import User, VerificationStatus
from app.schemas.invite_token import (
    ConfirmInviteRequest,
    CreateInviteTokenRequest,
    InviteTokenListResponse,
    InviteTokenResponse,
)
from app.schemas.public_offering import PublicInvitePreview
from app.services.events import log_event
from app.services.flags import (
    count_active_tokens,
    maybe_flag_redemption_rate,
    maybe_flag_manager_minor_skew,
)
from app.services.notifications import create_notification
from app.services.public_offering import get_offering_by_slug
from app.services.storage import get_public_url, put_object
from app.services.threads import create_promoter_connection_thread

router = APIRouter(tags=["invite-tokens"])

FRONTEND_BASE = settings.frontend_base_url


def _share_url(token: str) -> str:
    return f"{FRONTEND_BASE}/i/{token}"


def _token_response(row: InviteToken) -> InviteTokenResponse:
    return InviteTokenResponse(
        id=row.id,
        token=row.token,
        act_id=row.act_id,
        max_uses=row.max_uses,
        use_count=row.use_count,
        expires_at=row.expires_at,
        revoked_at=row.revoked_at,
        created_at=row.created_at,
        share_url=_share_url(row.token),
    )


@router.post(
    "/invites/tokens",
    response_model=InviteTokenResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_invite_token(
    payload: CreateInviteTokenRequest,
    db: Session = Depends(get_db),
    act_owner: User = Depends(require_act_owner),
) -> InviteTokenResponse:
    if count_active_tokens(db, act_owner.id) >= 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum active invite tokens reached",
        )
    if payload.act_id is not None:
        act = db.scalar(
            select(Act).where(Act.id == payload.act_id, Act.act_owner_id == act_owner.id)
        )
        if act is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Act not found")

    token_value = secrets.token_urlsafe(24)
    expires_at = datetime.now(UTC) + timedelta(days=payload.expires_in_days)
    row = InviteToken(
        act_owner_id=act_owner.id,
        act_id=payload.act_id,
        token=token_value,
        max_uses=payload.max_uses,
        expires_at=expires_at,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _token_response(row)


@router.get("/invites/tokens", response_model=InviteTokenListResponse)
def list_invite_tokens(
    db: Session = Depends(get_db),
    act_owner: User = Depends(require_act_owner),
) -> InviteTokenListResponse:
    rows = list(
        db.scalars(
            select(InviteToken)
            .where(InviteToken.act_owner_id == act_owner.id)
            .order_by(InviteToken.created_at.desc())
        ).all()
    )
    return InviteTokenListResponse(items=[_token_response(r) for r in rows])


@router.delete("/invites/tokens/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_invite_token(
    token_id: uuid.UUID,
    db: Session = Depends(get_db),
    act_owner: User = Depends(require_act_owner),
) -> None:
    row = db.get(InviteToken, token_id)
    if row is None or row.act_owner_id != act_owner.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token not found")
    row.revoked_at = datetime.now(UTC)
    db.commit()


@router.get("/public/invites/{token}", response_model=PublicInvitePreview)
def get_public_invite(
    token: str,
    db: Session = Depends(get_db),
    src: str | None = None,
) -> PublicInvitePreview:
    row = db.scalar(
        select(InviteToken)
        .options(selectinload(InviteToken.owner), selectinload(InviteToken.act))
        .where(InviteToken.token == token)
    )
    log_event(db, "invite_landing_view", invite_token=token, src=src)
    db.commit()

    if row is None:
        return PublicInvitePreview(
            owner_first_name="",
            act_owner_verified=False,
            act_names=[],
            token_valid=False,
        )

    now = datetime.now(UTC)
    expired = row.expires_at <= now
    revoked = row.revoked_at is not None
    exhausted = row.use_count >= row.max_uses
    valid = not expired and not revoked and not exhausted

    act_names: list[str] = []
    if row.act is not None:
        act_names = [row.act.name]
    elif valid:
        acts = list(
            db.scalars(select(Act).where(Act.act_owner_id == row.act_owner_id)).all()
        )
        act_names = [a.name for a in acts]

    return PublicInvitePreview(
        owner_first_name=row.act_owner.first_name,
        act_owner_verified=row.act_owner.verification_status == VerificationStatus.VERIFIED,
        act_names=act_names,
        token_valid=valid,
        expired=expired,
        revoked=revoked,
    )


@router.post("/invites/tokens/{token}/redeem", response_model=dict)
def redeem_invite_token(
    token: str,
    db: Session = Depends(get_db),
    rider: User = Depends(require_verified),
) -> dict:
    if rider.is_minor and rider.guardian_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Minor accounts require a verified guardian",
        )

    now = datetime.now(UTC)
    result = db.execute(
        update(InviteToken)
        .where(
            InviteToken.token == token,
            InviteToken.use_count < InviteToken.max_uses,
            InviteToken.revoked_at.is_(None),
            InviteToken.expires_at > now,
        )
        .values(use_count=InviteToken.use_count + 1)
        .returning(InviteToken.id, InviteToken.act_owner_id, InviteToken.act_id)
    ).first()
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invite token is invalid or exhausted",
        )

    token_id, act_owner_id, _act_id = result
    owner = db.get(User, act_owner_id)
    if owner is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Owner not found")

    if rider.is_minor:
        invite_status = PromoterConnectionStatus.PENDING_GUARDIAN
    else:
        invite_status = PromoterConnectionStatus.PENDING_ACT_OWNER_CONFIRM

    invite = PromoterConnection(
        act_owner_id=act_owner_id,
        booker_id=rider.id,
        invite_token_id=token_id,
        invitee_email=rider.email,
        status=invite_status,
        accepted_at=datetime.now(UTC),
    )
    db.add(invite)
    db.flush()

    rider_name = f"{rider.first_name} {rider.last_name}".strip() or rider.email
    create_notification(
        db,
        act_owner_id,
        "invite_redeemed",
        f"{rider_name} redeemed your invite link",
        {"promoter_connection_id": str(invite.id), "booker_id": str(rider.id)},
    )
    maybe_flag_redemption_rate(db, act_owner_id)
    maybe_flag_manager_minor_skew(db, act_owner_id)
    db.commit()
    return {"promoter_connection_id": str(invite.id), "status": invite.status.value}


@router.post("/invites/{invite_id}/confirm")
def confirm_invite(
    invite_id: uuid.UUID,
    payload: ConfirmInviteRequest,
    db: Session = Depends(get_db),
    act_owner: User = Depends(require_act_owner),
) -> dict:
    invite = db.get(PromoterConnection, invite_id)
    if invite is None or invite.act_owner_id != act_owner.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")

    if invite.status not in (
        PromoterConnectionStatus.PENDING_ACT_OWNER_CONFIRM,
        PromoterConnectionStatus.PENDING_GUARDIAN,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invite cannot be confirmed in current status",
        )

    if payload.action == "decline":
        invite.status = PromoterConnectionStatus.DECLINED
        if invite.booker_id:
            create_notification(
                db,
                invite.booker_id,
                "invite_declined",
                f"{act_owner.first_name} declined your friend invite",
                {"promoter_connection_id": str(invite.id)},
            )
        db.commit()
        return {"status": invite.status.value}

    if invite.status == PromoterConnectionStatus.PENDING_GUARDIAN:
        rider = db.get(User, invite.booker_id) if invite.booker_id else None
        if rider is None or rider.guardian_user_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Guardian approval required",
            )
        if invite.guardian_approved_at is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Guardian has not approved this connection",
            )

    invite.status = PromoterConnectionStatus.ACTIVE
    invite.owner_confirmed_at = datetime.now(UTC)
    create_promoter_connection_thread(db, invite.id)

    if invite.booker_id:
        create_notification(
            db,
            invite.booker_id,
            "invite_confirmed",
            f"{act_owner.first_name} confirmed your friend connection",
            {"promoter_connection_id": str(invite.id)},
        )
    maybe_flag_manager_minor_skew(db, act_owner.id)
    db.commit()
    return {"status": invite.status.value, "thread_created": True}


@router.post("/invites/{invite_id}/guardian-approve")
def guardian_approve_invite(
    invite_id: uuid.UUID,
    db: Session = Depends(get_db),
    guardian: User = Depends(require_verified),
) -> dict:
    invite = db.get(PromoterConnection, invite_id)
    if invite is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")
    if invite.status != PromoterConnectionStatus.PENDING_GUARDIAN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invite is not awaiting guardian approval",
        )
    rider = db.get(User, invite.booker_id) if invite.booker_id else None
    if rider is None or rider.guardian_user_id != guardian.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the rider guardian")

    invite.guardian_approved_at = datetime.now(UTC)
    create_notification(
        db,
        invite.act_owner_id,
        "guardian_approved",
        f"Guardian approved connection for {rider.first_name}",
        {"promoter_connection_id": str(invite.id)},
    )
    db.commit()
    return {"status": invite.status.value, "guardian_approved_at": invite.guardian_approved_at.isoformat()}


@router.post(
    "/act-owner/offerings/{offering_id}/photos",
    status_code=status.HTTP_201_CREATED,
)
async def upload_offering_photo(
    offering_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    act_owner: User = Depends(require_act_owner),
) -> dict:
    offering = db.scalar(
        select(Offering).where(Offering.id == offering_id, Offering.act_owner_id == act_owner.id)
    )
    if offering is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offering not found")

    raw = await file.read()
    image = Image.open(BytesIO(raw))
    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")

    primary_buf = BytesIO()
    image.save(primary_buf, format="JPEG", exif=b"")
    primary_key = f"offerings/{offering_id}/{uuid.uuid4()}.jpg"
    put_object(primary_key, primary_buf.getvalue())

    thumb = image.copy()
    thumb.thumbnail((400, 400))
    thumb_buf = BytesIO()
    thumb.save(thumb_buf, format="JPEG", exif=b"")
    thumb_key = f"offerings/{offering_id}/{uuid.uuid4()}_thumb.jpg"
    put_object(thumb_key, thumb_buf.getvalue())

    moderation = (
        ModerationStatus.PENDING
        if settings.photo_moderation_enabled
        else ModerationStatus.APPROVED
    )
    photo = OfferingPhoto(
        offering_id=offering_id,
        storage_key=primary_key,
        thumbnail_key=thumb_key,
        moderation_status=moderation,
        is_primary=False,
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return {
        "id": str(photo.id),
        "url": get_public_url(primary_key),
        "thumbnail_url": get_public_url(thumb_key),
    }
