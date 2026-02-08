from fastapi import APIRouter, Depends

from services.order import OrderService

router = APIRouter()

@router.post("/orders")
async def create_order(
    user_id: int,
    order_service: OrderService,
):
    return await order_service.create_order_from_cart(user_id)