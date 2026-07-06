from fastapi import HTTPException, status

from app.models.genre import Genre, GenreCatalog

ALLOWED_GENRES = {member.value for member in Genre}


def normalize_genres(raw: list[str]) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []
    for value in raw:
        if value not in ALLOWED_GENRES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid genre: {value}",
            )
        if value in seen:
            continue
        seen.add(value)
        normalized.append(value)
    return normalized


def require_act_genres(genre_catalog: GenreCatalog, genres: list[str]) -> list[str]:
    normalized = normalize_genres(genres)
    if len(normalized) < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Acts require at least one genre",
        )
    return normalized
