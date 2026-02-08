from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.crud import movies as crud_movies
from src.db import get_db
from src.schemas.movie import CertificationCreate, CertificationRead, CertificationUpdate
from src.dependencies.permissions import require_moderator


router = APIRouter(prefix="/certifications", tags=["Certifications"])


@router.get("/", response_model=list[CertificationRead])
async def list_certifications(db: AsyncSession = Depends(get_db)):
    return await crud_movies.list_certifications(db)


@router.get("/{certification_id}", response_model=CertificationRead)
async def get_certification(certification_id: int, db: AsyncSession = Depends(get_db)):
    cert = await crud_movies.get_certification(db, certification_id)
    if not cert:
        raise HTTPException(status_code=404, detail="Certification not found")
    return cert


@router.post(
    "/",
    response_model=CertificationRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_moderator)]
)
async def create_certification(payload: CertificationCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await crud_movies.create_certification(db, payload.name)
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Certification with this name already exists")


@router.patch(
    "/{certification_id}",
    response_model=CertificationRead,
    dependencies=[Depends(require_moderator)]
)
async def update_certification(
        certification_id: int,
        payload: CertificationUpdate,
        db: AsyncSession = Depends(get_db)
):
    cert = await crud_movies.get_certification(db, certification_id)
    if not cert:
        raise HTTPException(status_code=404, detail="Certification not found")
    try:
        return await crud_movies.update_certification(db, cert, payload.name)
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Certification with this name already exists")


@router.delete(
    "/{certification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_moderator)]
)
async def delete_certification(certification_id: int, db: AsyncSession = Depends(get_db)):
    cert = await crud_movies.get_certification(db, certification_id)
    if not cert:
        raise HTTPException(status_code=404, detail="Certification not found")

    try:
        await crud_movies.delete_certification(db, cert)
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Certification can't be deleted due to related records")
    return None
