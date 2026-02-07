from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas import OrderItemReadSchema, OrderReadSchema
from src.models import OrderItem, Order


class CrudOrder:
    def __init__(self, db: AsyncSession):
        self.db = db


class CrudOrderItem:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_order_item_by_id(self, order_item_id: int) -> OrderItem | None:
        stmt = select(OrderItem).where(OrderItem.id == order_item_id)

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()


    async def create_order_item(self, order_id: int, movie_id: int, price: int) -> OrderItem:
        db_order_item = OrderItem(
            order_id=order_id,
            movie_id=movie_id,
            price_at_order=price
        )

        self.db.add(db_order_item)
        await self.db.commit()
        await self.db.refresh(db_order_item)
        return db_order_item

    async def get_order_by_order_item(self, order_id: int) -> Order:
        stmt = select(Order).where(Order.id == order_id)

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_order_item(self, order_item_id: int) -> bool:
        db_order_item = await self.get_order_item_by_id(order_item_id=order_item_id)

        if not db_order_item:
            return False

        await self.db.delete(db_order_item)
        await self.db.commit()
        return True
