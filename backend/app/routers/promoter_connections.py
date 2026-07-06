from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.dependencies import require_act_owner, require_booker, require_verified
from app.models.promoter_connection import PromoterConnection, PromoterConnectionStatus
from app.models.user import User, VerificationStatus
from app.schemas.promoter_connection import (
    CreatePromoterConnectionRequest,
    PromoterConnectionListResponse,
    PromoterConnectionResponse,
    UpdatePromoterConnectionStatusRequest,
)
from app.services.threads import create_promoter_connection_thread

router = APIRouter(tags=["promoter-connections"])


def _invite_to_response(invite: PromoterConnection) -> PromoterConnectionResponse:
    return PromoterConnectionResponse(
        id=invite.id,
        act_owner_id=invite.act_owner_id,
        booker_id=invite.booker_id,
        invitee_email=invite.invitee_email,
        status=invite.status.value,
        invited_at=invite.invited_at,
        accepted_at=invite.accepted_at,
        created_at=invite.created_at,
    )


@router.post(
    "/act-owner/promoter-connections",
    response_model=PromoterConnectionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_promoter_connection(
    payload: CreatePromoterConnectionRequest,
    db: Session = Depends(get_db),
    act_owner: User = Depends(require_act_owner),
) -> PromoterConnectionResponse:
    email = payload.invitee_email.lower().strip()
    if email == act_owner.email.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot invite yourself",
        )

    existing = db.scalar(
        select(PromoterConnection).where(
            PromoterConnection.act_owner_id == act_owner.id,
            func.lower(PromoterConnection.invitee_email) == email,
            PromoterConnection.status == PromoterConnectionStatus.PENDING_ACT_OWNER_CONFIRM,
            PromoterConnection.invite_token_id.is_(None),
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A pending invite already exists for this email",
        )

    rider = db.scalar(select(User).where(func.lower(User.email) == email))
    booker_id = rider.id if rider else None
    if rider is not None and rider.verification_status != VerificationStatus.VERIFIED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitee must complete identity verification before accepting",
        )

    invite = PromoterConnection(
        act_owner_id=act_owner.id,
        booker_id=booker_id,
        invitee_email=email,
        status=PromoterConnectionStatus.PENDING_ACT_OWNER_CONFIRM,
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return _invite_to_response(invite)


@router.get("/act-owner/promoter-connections", response_model=PromoterConnectionListResponse)
def list_owner_promoter_connections(
    db: Session = Depends(get_db),
    act_owner: User = Depends(require_act_owner),
) -> PromoterConnectionListResponse:
    invites = list(
        db.scalars(
            select(PromoterConnection)
            .where(PromoterConnection.act_owner_id == act_owner.id)
            .order_by(PromoterConnection.created_at.desc())
        ).all()
    )
    return PromoterConnectionListResponse(items=[_invite_to_response(i) for i in invites])


@router.patch(
    "/act-owner/promoter-connections/{invite_id}",
    response_model=PromoterConnectionResponse,
)
def owner_update_promoter_connection(
    invite_id: UUID,
    payload: UpdatePromoterConnectionStatusRequest,
    db: Session = Depends(get_db),
    act_owner: User = Depends(require_act_owner),
) -> PromoterConnectionResponse:
    invite = db.get(PromoterConnection, invite_id)
    if invite is None or invite.act_owner_id != act_owner.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")
    if payload.status != "revoked":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Owners may only revoke invites",
        )
    if invite.status not in (
        PromoterConnectionStatus.PENDING_ACT_OWNER_CONFIRM,
        PromoterConnectionStatus.PENDING_GUARDIAN,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invite is no longer pending",
        )
    invite.status = PromoterConnectionStatus.REVOKED
    db.commit()
    db.refresh(invite)
    return _invite_to_response(invite)


@router.get("/booker/promoter-connections", response_model=PromoterConnectionListResponse)
def list_rider_promoter_connections(
    db: Session = Depends(get_db),
    rider: User = Depends(require_booker),
) -> PromoterConnectionListResponse:
    invites = list(
        db.scalars(
            select(PromoterConnection).where(
                (PromoterConnection.booker_id == rider.id)
                | (func.lower(PromoterConnection.invitee_email) == rider.email.lower())
            ).order_by(PromoterConnection.created_at.desc())
        ).all()
    )
    return PromoterConnectionListResponse(items=[_invite_to_response(i) for i in invites])


@router.patch(
    "/booker/promoter-connections/{invite_id}/respond",
    response_model=PromoterConnectionResponse,
)
def rider_respond_promoter_connection(
    invite_id: UUID,
    payload: UpdatePromoterConnectionStatusRequest,
    db: Session = Depends(get_db),
    rider: User = Depends(require_booker),
) -> PromoterConnectionResponse:
    if payload.status not in ("accepted", "declined"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Riders may only accept or decline",
        )
    invite = db.get(PromoterConnection, invite_id)
    if invite is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")
    if invite.booker_id not in (None, rider.id) and invite.invitee_email.lower() != rider.email.lower():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your invite")
    if invite.invite_token_id is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token-based invites are confirmed by the owner",
        )
    if invite.status != PromoterConnectionStatus.PENDING_ACT_OWNER_CONFIRM:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invite is no longer pending",
        )
    invite.booker_id = rider.id
    if payload.status == "accepted":
        invite.status = PromoterConnectionStatus.ACTIVE
        invite.accepted_at = datetime.now(UTC)
        invite.owner_confirmed_at = datetime.now(UTC)
        create_promoter_connection_thread(db, invite.id)
    else:
        invite.status = PromoterConnectionStatus.DECLINED
    db.commit()
    db.refresh(invite)
    return _invite_to_response(invite)


def get_active_promoter_connection(
    db: Session, act_owner_id: UUID, booker_id: UUID
) -> PromoterConnection | None:
    return db.scalar(
        select(PromoterConnection).where(
            PromoterConnection.act_owner_id == act_owner_id,
            PromoterConnection.booker_id == booker_id,
            PromoterConnection.status == PromoterConnectionStatus.ACTIVE,
        )
    )


# Backwards-compatible alias
get_accepted_promoter_connection = get_active_promoter_connection
