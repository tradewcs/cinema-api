from typing import Sequence, List

from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.enums import OrderStatus
from src.models import OrderItem, Order


class CrudOrder:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_order_by_id(self, order_id: int) -> Order | None:
        stmt = select(Order).where(Order.id == order_id)

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_orders(self, user_id: int) -> Sequence[Order]:
        stmt = select(Order).where(Order.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def create_order(self, user_id: int) -> Order:
        db_order = Order(
            user_id=user_id,
            status=OrderStatus.PENDING,
            total_amount=None
        )
        self.db.add(db_order)
        await self.db.commit()
        await self.db.refresh(db_order)

        return db_order

    async def update_order_status(self, order_id: int, new_status: OrderStatus) -> Order | None:
        order = await self.get_order_by_id(order_id)

        if not order:
            return None

        order.status = new_status

        await self.db.commit()
        await self.db.refresh(order)

        return order

    async def update_order_total_amount(self, order_id: int,
                                  amount: float) -> Order | None:
        order = await self.get_order_by_id(order_id)

        if not order:
            return None

        order.total_amount = amount

        await self.db.commit()
        await self.db.refresh(order)

        return order

    async def delete_order(self, order_id: int) -> bool:
        order = await self.get_order_by_id(order_id)
        if not order:
            return False

        await self.db.delete(order)
        await self.db.commit()
        return True


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

    async def bulk_create_order_item(self, items_data: List[dict]) -> None:
        stmt = insert(OrderItem).values(items_data)

        await self.db.execute(stmt)
        await self.db.commit()

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
