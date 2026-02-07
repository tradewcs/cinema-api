from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.models import Payment


class PaymentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, payment_id: int) -> Payment | None:
        stmt = (
            select(Payment)
            .where(Payment.id == payment_id)
            .options(
                joinedload(Payment.user),
                joinedload(Payment.order),
                joinedload(Payment.payment_items),
            )
        )

        return await self.db.scalar(stmt)

    async def get_all(self, skip: int = 0, limit: int | None = None) -> list[Payment]:
        stmt = select(Payment).offset(skip).order_by(Payment.created_at)
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count(self) -> int:
        query = select(func.count()).select_from(Payment)
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def create(self, **kwargs: Any) -> Payment:
        instance = Payment(**kwargs)
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def update(self, instance: Payment, **kwargs: Any) -> Payment:
        for key, value in kwargs.items():
            if value is not None:
                setattr(instance, key, value)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def delete(self, instance: Payment) -> None:
        await self.db.delete(instance)
        await self.db.flush()

    async def get_by_external_payment_id(
        self, external_payment_id: str
    ) -> Payment | None:
        stmt = (
            select(Payment)
            .where(Payment.external_payment_id == external_payment_id)
            .options(joinedload(Payment.payment_items))
        )
        return await self.db.scalar(stmt)
