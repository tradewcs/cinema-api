import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories import movies as crud_movies
from src.db import get_db
from src.schemas.movie import MovieCreate, MovieRead, MovieUpdate, MoviesPage, PageMeta
from src.dependencies.permissions import require_moderator

router = APIRouter(prefix="/movies", tags=["Movies"])


@router.get("/", response_model=MoviesPage)
async def list_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    q: str | None = Query(None, min_length=1),
    year_from: int | None = Query(None, ge=1888, le=2100),
    year_to: int | None = Query(None, ge=1888, le=2100),
    imdb_from: float | None = Query(None, ge=0, le=10),
    imdb_to: float | None = Query(None, ge=0, le=10),
    certification_id: int | None = Query(None, ge=1),
    sort_by: str = Query("id"),
    sort_dir: str = Query("desc"),
    db: AsyncSession = Depends(get_db),
):
    items, total_items = await crud_movies.list_movies(
        db,
        page=page,
        per_page=per_page,
        q=q,
        year_from=year_from,
        year_to=year_to,
        imdb_from=imdb_from,
        imdb_to=imdb_to,
        certification_id=certification_id,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
    total_pages = math.ceil(total_items / per_page) if total_items else 0
    return {
        "items": items,
        "meta": PageMeta(
            page=page,
            per_page=per_page,
            total_items=total_items,
            total_pages=total_pages,
        ),
    }


@router.get("/{movie_id}", response_model=MovieRead)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await crud_movies.get_movie(db, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie


@router.post(
    "/",
    response_model=MovieRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_moderator)],
)
async def create_movie(payload: MovieCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await crud_movies.create_movie(db, payload)
    except ValueError as e:
        msg = str(e)
        if msg == "CERTIFICATION_NOT_FOUND":
            raise HTTPException(status_code=404, detail="Certification not found")
        if msg.startswith("MISSING_RELATED:"):
            raise HTTPException(status_code=404, detail=msg)
        raise
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Movie already exists (name+year+time must be unique)",
        )


@router.patch(
    "/{movie_id}", response_model=MovieRead, dependencies=[Depends(require_moderator)]
)
async def update_movie(
    movie_id: int, payload: MovieUpdate, db: AsyncSession = Depends(get_db)
):
    movie = await crud_movies.get_movie(db, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    try:
        return await crud_movies.update_movie(db, movie, payload)
    except ValueError as e:
        msg = str(e)
        if msg == "CERTIFICATION_NOT_FOUND":
            raise HTTPException(status_code=404, detail="Certification not found")
        if msg.startswith("MISSING_RELATED:"):
            raise HTTPException(status_code=404, detail=msg)
        raise
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Movie already exists (name+year+time must be unique)",
        )


@router.delete(
    "/{movie_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_moderator)],
)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await crud_movies.get_movie(db, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    try:
        await crud_movies.delete_movie(db, movie)
    except ValueError as e:
        if str(e) == "MOVIE_PURCHASED":
            raise HTTPException(
                status_code=409,
                detail="Movie can't be deleted because it has been purchased",
            )
        raise
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Movie can't be deleted due to related records",
        )
    return None
