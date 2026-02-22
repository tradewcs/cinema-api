from typing import List, Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_db
from src.dependencies.services import PaymentServiceDep
from src.dependencies.user import get_current_user
from src.exceptions import (
    OrderNotFoundError,
    PaymentNotAllowed,
    PaymentAmountMismatch,
    PaymentSessionError,
)
from src.models import User
from src.schemas import OrderReadSchema
from src.schemas.order import OrderListSchema
from src.services.interfaces import PaymentProcessorInterface
from src.services.order import OrderService

router = APIRouter()


@router.post("/add", response_model=OrderReadSchema)
async def create_order(
    payment_service: PaymentServiceDep,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OrderService(db)
    try:
        return await service.create_order_from_cart(
            user_id=current_user.id, payment_service=payment_service
        )
    except OrderNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order not found",
        )
    except PaymentNotAllowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order is invalid",
        )
    except PaymentAmountMismatch:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment amount mismatches with order amount",
        )
    except PaymentSessionError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Some error while creating payment session occurred",
        )


@router.get("/all", response_model=List[OrderListSchema])
async def list_orders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OrderService(db)

    orders = await service.get_orders(user_id=current_user.id)

    return orders
