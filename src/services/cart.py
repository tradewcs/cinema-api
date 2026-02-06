from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from src.crud.cart import CRUDCart
from src.exceptions.cart import (
    CartItemAlreadyExistsError,
    MovieAlreadyPurchasedError,
    MovieNotAvailableError,
    CartNotFoundError
)


class CartService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.cart_crud = CRUDCart(db)

    async def get_user_cart(self, user_id: int):
        cart = await self.cart_crud.get_cart_by_user_id(user_id=user_id)
        if not cart:
            raise CartNotFoundError()

        total_items = len(cart.items)
        total_price = sum((item.movie.price for item in cart.items), Decimal("0.00"))

        return {
            "id": cart.id,
            "user_id": cart.user_id,
            "items": cart.items,
            "total_items": total_items,
            "total_price": total_price
        }

    async def add_item_to_cart(self, user_id: int, movie_id: int):
        # TODO
        # movie = await movie_crud.get_by_id(self.db, movie_id=movie_id)
        # if not movie:
        #     raise MovieNotAvailableError()
        # TODO
        # is_purchased = await order_crud.check_if_purchased(
        #     self.db, user_id=user_id, movie_id=movie_id
        # )
        # if is_purchased:
        #     raise MovieAlreadyPurchasedError()

        cart = await self.cart_crud.get_or_create_cart(user_id=user_id)

        if any(item.movie_id == movie_id for item in cart.items):
            raise CartItemAlreadyExistsError()

        return await self.cart_crud.add_item_to_cart(cart_id=cart.id, movie_id=movie_id)