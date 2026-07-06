from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.genre import Genre


class ActCreateRequest(BaseModel):
    genre_id: UUID
    name: str = Field(min_length=1, max_length=128)
    act_type: str | None = Field(default=None, max_length=128)
    years_active: int | None = Field(default=None, ge=0, le=100)
    description: str | None = Field(default=None, max_length=5000)
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    address: str = Field(min_length=1, max_length=512)
    photo_urls: list[str] = Field(default_factory=list)
    genres: list[Genre] = Field(default_factory=list)

    @field_validator("genres")
    @classmethod
    def unique_genres(cls, values: list[Genre]) -> list[Genre]:
        seen: set[Genre] = set()
        unique: list[Genre] = []
        for value in values:
            if value not in seen:
                seen.add(value)
                unique.append(value)
        return unique


class ActUpdateRequest(BaseModel):
    genre_id: UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=128)
    act_type: str | None = Field(default=None, max_length=128)
    years_active: int | None = Field(default=None, ge=0, le=100)
    description: str | None = Field(default=None, max_length=5000)
    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)
    address: str | None = Field(default=None, min_length=1, max_length=512)
    photo_urls: list[str] | None = None
    genres: list[Genre] | None = None

    @field_validator("genres")
    @classmethod
    def unique_genres(
        cls, values: list[Genre] | None
    ) -> list[Genre] | None:
        if values is None:
            return None
        seen: set[Genre] = set()
        unique: list[Genre] = []
        for value in values:
            if value not in seen:
                seen.add(value)
                unique.append(value)
        return unique


class ActResponse(BaseModel):
    id: UUID
    act_owner_id: UUID
    genre_id: UUID
    name: str
    act_type: str | None
    years_active: int | None
    description: str | None
    lat: float
    lng: float
    address: str
    photo_urls: list[str]
    genres: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}
