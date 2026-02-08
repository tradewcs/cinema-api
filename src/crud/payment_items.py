from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import insert

from src.models.payments import PaymentItem
from src.models.order import OrderItem


class PaymentItemRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, payment_item_id: int) -> PaymentItem | None:
        stmt = (
            select(PaymentItem)
            .where(PaymentItem.id == payment_item_id)
            .options(
                joinedload(PaymentItem.order_item),
                joinedload(PaymentItem.payment),
            )
        )

        return await self.db.scalar(stmt)

    async def get_all(
        self, skip: int = 0, limit: int | None = None
    ) -> list[PaymentItem]:
        stmt = select(PaymentItem).offset(skip).order_by(PaymentItem.id)
        if limit is not None:
            stmt = stmt.limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count(self) -> int:
        query = select(func.count()).select_from(PaymentItem)
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def create(self, **kwargs: Any) -> PaymentItem:
        instance = PaymentItem(**kwargs)
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def update(self, instance: PaymentItem, **kwargs: Any) -> PaymentItem:
        for key, value in kwargs.items():
            if value is not None:
                setattr(instance, key, value)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def delete(self, instance: PaymentItem) -> None:
        await self.db.delete(instance)
        await self.db.flush()

    async def create_from_order_items(
        self, payment_id: int, order_items: list[OrderItem]
    ) -> list[PaymentItem]:
        rows = [
            {
                "payment_id": payment_id,
                "order_item_id": item.id,
                "price_at_payment": item.price_at_order,
            }
            for item in order_items
        ]

        stmt = insert(PaymentItem).returning(PaymentItem)
        items = await self.db.execute(stmt, rows)

        return list(items.all())
