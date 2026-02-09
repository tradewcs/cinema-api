from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_db
from src.dependencies.user import get_current_user
from src.models import User
from src.schemas import OrderReadSchema
from src.services.order import OrderService

router = APIRouter()

@router.post("/add")
async def create_order(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await OrderService(db).create_order_from_cart(user_id=current_user.id)

@router.get("/all", response_model=List[OrderReadSchema])
async def list_orders(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    return await OrderService(db).get_orders(user_id=current_user.id)