from decimal import Decimal
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.repositories.order import CrudOrder, CrudOrderItem
from src.exceptions.order import (
    CartEmptyError,
    CartNotFoundError,
    OrdersNotExistError
)

from src.services.cart import CartService


class OrderService:
    def __init__(
        self,
        db: AsyncSession,
    ):
        self.db = db
        self.cart_service = CartService(db)
        self.order_crud = CrudOrder(db)
        self.order_item_crud = CrudOrderItem(db)

    async def create_order_from_cart(self, user_id: int):
        cart_data = await self.cart_service.get_user_cart(user_id=user_id)

        if not cart_data:
            raise CartNotFoundError()

        if not cart_data["items"]:
            raise CartEmptyError()

        cart_items = cart_data["items"]

        order = await self.order_crud.create_order(user_id=user_id)

        order_items_data = [
            {
                "order_id": order.id,
                "movie_id": item.movie_id,
                "price_at_order": item.movie.price,
            }
            for item in cart_items
        ]

        await self.order_item_crud.bulk_create_order_item(order_items_data)

        total = sum(
            Decimal(str(item.movie.price)) for item in cart_items
        )

        await self.order_crud.update_order_total_amount(
            order_id=order.id,
            amount=total
        )

        await self.cart_service.clear_user_cart(user_id=user_id)

        return order

    async def get_orders(self, user_id: int):
        orders = await self.order_crud.get_all_orders(user_id=user_id)

        if not orders:
            raise OrdersNotExistError()

        return orders
