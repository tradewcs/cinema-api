from fastapi import APIRouter, Depends, HTTPException, status, Security
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories import movies as crud_movies
from src.db import get_db
from src.dependencies.user import get_admin_user
from src.schemas.movie import DirectorCreate, DirectorRead, DirectorUpdate
from src.models.accounts import User

router = APIRouter(prefix="/directors", tags=["Directors"])


@router.get("/", response_model=list[DirectorRead])
async def list_directors(db: AsyncSession = Depends(get_db)):
    return await crud_movies.list_directors(db)


@router.get("/{director_id}", response_model=DirectorRead)
async def get_director(director_id: int, db: AsyncSession = Depends(get_db)):
    director = await crud_movies.get_director(db, director_id)
    if not director:
        raise HTTPException(status_code=404, detail="Director not found")
    return director


@router.post(
    "/",
    response_model=DirectorRead,
    status_code=status.HTTP_201_CREATED
)
async def create_director(
    payload: DirectorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Security(get_admin_user)
):
    """
    Create a new director. Requires admin or moderator privileges.
    """
    try:
        return await crud_movies.create_director(db, payload.name)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Director with this name already exists"
        )


@router.patch("/{director_id}", response_model=DirectorRead)
async def update_director(
    director_id: int,
    payload: DirectorUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Security(get_admin_user)
):
    """
    Update an existing director. Requires admin or moderator privileges.
    """
    director = await crud_movies.get_director(db, director_id)
    if not director:
        raise HTTPException(status_code=404, detail="Director not found")
    try:
        return await crud_movies.update_director(db, director, payload.name)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Director with this name already exists"
        )


@router.delete("/{director_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_director(
    director_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Security(get_admin_user)
):
    """
    Delete a director. Requires admin or moderator privileges.
    """
    director = await crud_movies.get_director(db, director_id)
    if not director:
        raise HTTPException(status_code=404, detail="Director not found")

    try:
        await crud_movies.delete_director(db, director)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Director can't be deleted due to related records"
        )
    return None
