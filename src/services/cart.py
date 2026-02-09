from decimal import Decimal
from typing import Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.cart import CRUDCart
from src.models.movie import Movie
from src.models.order import Order, OrderItem
from src.enums.order_status import OrderStatus
from src.exceptions.cart import (
    CartItemAlreadyExistsError,
    MovieAlreadyPurchasedError,
    MovieNotAvailableError,
    CartNotFoundError,
)


class CartService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.cart_crud = CRUDCart(db)

    async def get_user_cart(self, user_id: int) -> Dict[str, Any]:
        """
        Retrieves the cart for a specific user and calculates totals.
        """
        cart = await self.cart_crud.get_or_create_cart(user_id=user_id)

        total_items = len(cart.items)
        total_price = sum((item.movie.price for item in cart.items), Decimal("0.00"))

        return {
            "id": cart.id,
            "user_id": cart.user_id,
            "items": cart.items,
            "total_items": total_items,
            "total_price": total_price,
        }

    async def add_item_to_cart(self, user_id: int, movie_id: int) -> Dict[str, Any]:
        """
        Validates movie availability and purchase status before adding to cart.
        """
        movie_result = await self.db.execute(select(Movie).where(Movie.id == movie_id))
        movie = movie_result.scalar_one_or_none()
        if not movie:
            raise MovieNotAvailableError()

        purchase_check = await self.db.execute(
            select(OrderItem)
            .join(Order)
            .where(
                Order.user_id == user_id,
                Order.status == OrderStatus.PAID,
                OrderItem.movie_id == movie_id,
            )
        )
        if purchase_check.scalar_one_or_none():
            raise MovieAlreadyPurchasedError()

        cart = await self.cart_crud.get_or_create_cart(user_id=user_id)

        if any(item.movie_id == movie_id for item in cart.items):
            raise CartItemAlreadyExistsError()

        await self.cart_crud.add_item_to_cart(cart_id=cart.id, movie_id=movie_id)
        return await self.get_user_cart(user_id=user_id)

    async def remove_from_cart(self, user_id: int, movie_id: int) -> Dict[str, Any]:
        """
        Removes a specific movie from the user's cart.
        """
        cart = await self.cart_crud.get_cart_by_user_id(user_id=user_id)
        if not cart:
            raise CartNotFoundError()

        deleted = await self.cart_crud.remove_item(cart_id=cart.id, movie_id=movie_id)
        if not deleted:
            raise MovieNotAvailableError()

        return await self.get_user_cart(user_id=user_id)

    async def clear_user_cart(self, user_id: int) -> Dict[str, Any]:
        """
        Deletes all items from the user's cart.
        """
        cart = await self.cart_crud.get_cart_by_user_id(user_id=user_id)
        if not cart:
            raise CartNotFoundError()

        await self.cart_crud.clear_cart(cart_id=cart.id)
        return await self.get_user_cart(user_id=user_id)
