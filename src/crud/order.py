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

    def create_order_item(self, order_id: int, movie_id: int, price: int) -> OrderItem:
        db_order_item = OrderItem(
            order_id=order_id,
            movie_id=movie_id,
            price_at_order=price
        )

        self.db.add(db_order_item)
        self.db.commit()
        self.db.refresh(db_order_item)
        return db_order_item

    async def get_order_by_order_item(self, order_id: int):
        stmt = select(Order).where(Order.id == order_id)

        result = await self.db.execute(stmt)
        order = result.scalar_one_or_none()
        return OrderReadSchema.model_validate(order)
