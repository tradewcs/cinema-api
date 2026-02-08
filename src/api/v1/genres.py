from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories import movies as crud_movies
from src.db import get_db
from src.schemas.movie import GenreCreate, GenreRead, GenreUpdate
from src.dependencies.permissions import require_moderator

router = APIRouter(prefix="/genres", tags=["Genres"])


@router.get("/", response_model=list[GenreRead])
async def list_genres(db: AsyncSession = Depends(get_db)):
    return await crud_movies.list_genres(db)


@router.get("/{genre_id}", response_model=GenreRead)
async def get_genre(genre_id: int, db: AsyncSession = Depends(get_db)):
    genre = await crud_movies.get_genre(db, genre_id)
    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found")
    return genre


@router.post(
    "/",
    response_model=GenreRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_moderator)],
)
async def create_genre(payload: GenreCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await crud_movies.create_genre(db, payload.name)
    except IntegrityError:
        raise HTTPException(
            status_code=409, detail="Genre with this name already exists"
        )


@router.patch(
    "/{genre_id}", response_model=GenreRead, dependencies=[Depends(require_moderator)]
)
async def update_genre(
    genre_id: int, payload: GenreUpdate, db: AsyncSession = Depends(get_db)
):
    genre = await crud_movies.get_genre(db, genre_id)
    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found")
    try:
        return await crud_movies.update_genre(db, genre, payload.name)
    except IntegrityError:
        raise HTTPException(
            status_code=409, detail="Genre with this name already exists"
        )


@router.delete(
    "/{genre_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_moderator)],
)
async def delete_genre(genre_id: int, db: AsyncSession = Depends(get_db)):
    genre = await crud_movies.get_genre(db, genre_id)
    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found")

    try:
        await crud_movies.delete_genre(db, genre)
    except IntegrityError:
        raise HTTPException(
            status_code=409, detail="Genre can't be deleted due to related records"
        )
    return None
