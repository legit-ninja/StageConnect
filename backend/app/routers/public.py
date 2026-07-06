from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.public_offering import PublicInvitePreview, PublicOffering
from app.services.events import log_event
from app.services.public_offering import get_offering_by_slug, offering_to_public

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/acts/{slug}", response_model=PublicOffering)
@router.get("/offerings/{slug}", response_model=PublicOffering)
def get_public_offering(
    slug: str,
    db: Session = Depends(get_db),
    src: str | None = None,
) -> PublicOffering:
    offering = get_offering_by_slug(db, slug)
    if offering is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offering not found")

    log_event(
        db,
        "public_offering_view",
        offering_slug=slug,
        src=src,
        payload={"active": offering.active},
    )
    db.commit()
    return offering_to_public(db, offering)
