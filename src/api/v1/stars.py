from fastapi import APIRouter, Depends, HTTPException, status, Security
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories import movies as crud_movies
from src.db import get_db
from src.models.accounts import User
from src.schemas.movie import StarCreate, StarRead, StarUpdate
from src.dependencies.user import get_admin_user

router = APIRouter(prefix="/stars", tags=["Stars"])


@router.get("/", response_model=list[StarRead])
async def list_stars(db: AsyncSession = Depends(get_db)):
    return await crud_movies.list_stars(db)


@router.get("/{star_id}", response_model=StarRead)
async def get_star(star_id: int, db: AsyncSession = Depends(get_db)):
    star = await crud_movies.get_star(db, star_id)
    if not star:
        raise HTTPException(status_code=404, detail="Star not found")
    return star


@router.post(
    "/",
    response_model=StarRead,
    status_code=status.HTTP_201_CREATED
)
async def create_star(
    payload: StarCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Security(get_admin_user)
):
    """
    Create a new star. Requires admin or moderator privileges.
    """
    try:
        return await crud_movies.create_star(db, payload.name)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Star with this name already exists"
        )


@router.patch("/{star_id}", response_model=StarRead)
async def update_star(
    star_id: int,
    payload: StarUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Security(get_admin_user)
):
    """
    Update an existing star. Requires admin or moderator privileges.
    """
    star = await crud_movies.get_star(db, star_id)
    if not star:
        raise HTTPException(status_code=404, detail="Star not found")
    try:
        return await crud_movies.update_star(db, star, payload.name)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Star with this name already exists"
        )


@router.delete("/{star_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_star(
    star_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Security(get_admin_user)
):
    """
    Delete a star. Requires admin or moderator privileges.
    """
    star = await crud_movies.get_star(db, star_id)
    if not star:
        raise HTTPException(status_code=404, detail="Star not found")

    try:
        await crud_movies.delete_star(db, star)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Star can't be deleted due to related records"
        )
    return None
