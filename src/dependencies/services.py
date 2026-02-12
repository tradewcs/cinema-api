from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio.session import AsyncSession

from src.repositories.payment_items import PaymentItemRepository
from src.repositories.payments import PaymentRepository
from src.repositories.order import CrudOrder as OrderRepository
from src.db import get_db
from src.services.stripe_payments import StripePaymentProcessor


def get_stripe_payment_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StripePaymentProcessor:
    payment_repository = PaymentRepository(db)
    payment_item_repository = PaymentItemRepository(db)
    order_repository = OrderRepository(db)
    """Get service for payment logic."""
    return StripePaymentProcessor(
        db=db,
        payment_repo=payment_repository,
        payment_item_repo=payment_item_repository,
        order_repo=order_repository,
    )


PaymentServiceDep = Annotated[
    StripePaymentProcessor, Depends(get_stripe_payment_service)
]
