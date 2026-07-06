from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.genre import GenreCatalog
from app.schemas.genre_catalog import GenreResponse

router = APIRouter(prefix="/genres", tags=["genres"])


@router.get("", response_model=list[GenreResponse])
def list_genres(
    db: Session = Depends(get_db),
    active_in_ui: bool | None = Query(default=True),
) -> list[GenreCatalog]:
    stmt = select(GenreCatalog)
    if active_in_ui is not None:
        stmt = stmt.where(GenreCatalog.active_in_ui.is_(active_in_ui))
    return list(db.scalars(stmt.order_by(GenreCatalog.name)).all())
