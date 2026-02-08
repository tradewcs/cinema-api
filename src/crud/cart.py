from typing import Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.cart import Cart, CartItem

class CRUDCart:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_cart_by_user_id(self, user_id: int) -> Optional[Cart]:
        """
        Fetches the user's cart.
        """
        result = await self.db.execute(
            select(Cart).where(Cart.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_cart(self, user_id: int) -> Cart:
        """Creates a new empty cart for a user."""
        db_cart = Cart(user_id=user_id)
        self.db.add(db_cart)
        await self.db.commit()
        await self.db.refresh(db_cart)
        return db_cart

    async def get_or_create_cart(self, user_id: int) -> Cart:
        """Gets or creates a new empty cart for a user."""
        cart = await self.get_cart_by_user_id(user_id)
        if not cart:
            cart = await self.create_cart(user_id)
            cart.items = []
        return cart

    async def get_item_in_cart(self, cart_id: int, movie_id: int) -> Optional[CartItem]:
        """Checks if a specific movie is already in a specific cart."""
        result = await self.db.execute(
            select(CartItem).where(
                CartItem.cart_id == cart_id,
                CartItem.movie_id == movie_id
            )
        )
        return result.scalar_one_or_none()

    async def add_item_to_cart(self, cart_id: int, movie_id: int) -> CartItem:
        """Adds a movie to the cart items."""
        db_item = CartItem(cart_id=cart_id, movie_id=movie_id)
        self.db.add(db_item)
        await self.db.commit()
        await self.db.refresh(db_item)
        return db_item

    async def remove_item(self, cart_id: int, movie_id: int) -> bool:
        """Removes a specific movie from the cart."""
        result = await self.db.execute(
            delete(CartItem).where(
                CartItem.cart_id == cart_id,
                CartItem.movie_id == movie_id
            )
        )
        await self.db.commit()
        return result.rowcount > 0

    async def clear_cart(self, cart_id: int) -> None:
        """Removes all items from the user's cart."""
        await self.db.execute(
            delete(CartItem).where(CartItem.cart_id == cart_id)
        )
        await self.db.commit()
