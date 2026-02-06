from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GenreCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class GenreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class StarCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class StarRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class DirectorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class DirectorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class CertificationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class CertificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class MovieCreate(BaseModel):
    name: str = Field(min_length=1, max_length=250)
    year: int = Field(ge=1888, le=2100)
    time: int = Field(ge=1)
    imdb: float = Field(ge=0, le=10)
    votes: int = Field(ge=0)

    meta_score: float | None = None
    gross: float | None = None

    description: str = Field(min_length=1)

    price: Decimal | None = Field(default=None, ge=0)
    certification_id: int

    genre_ids: list[int] = Field(default_factory=list)
    director_ids: list[int] = Field(default_factory=list)
    star_ids: list[int] = Field(default_factory=list)


class MovieUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=250)
    year: int | None = Field(default=None, ge=1888, le=2100)
    time: int | None = Field(default=None, ge=1)
    imdb: float | None = Field(default=None, ge=0, le=10)
    votes: int | None = Field(default=None, ge=0)

    meta_score: float | None = None
    gross: float | None = None

    description: str | None = None

    price: Decimal | None = Field(default=None, ge=0)
    certification_id: int | None = None

    genre_ids: list[int] | None = None
    director_ids: list[int] | None = None
    star_ids: list[int] | None = None


class MovieRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    uuid: UUID

    name: str
    year: int
    time: int
    imdb: float
    votes: int

    meta_score: float | None
    gross: float | None

    description: str
    price: Decimal | None

    certification: CertificationRead
    genres: list[GenreRead] = Field(default_factory=list)
    directors: list[DirectorRead] = Field(default_factory=list)
    stars: list[StarRead] = Field(default_factory=list)
