from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
from src.enums import PaymentStatusEnum

from src.schemas.payments import (
    PaymentCreateSchema,
    RefundCreateSchema,
    PaymentSessionReadSchema,
    RefundStatusReadSchema,
    PaymentStatusReadSchema,
    PaymentReadSchema,
)


class PaymentProcessorInterface(ABC):
    """Іnterface for payment processors like Stripe, PayPal."""

    @abstractmethod
    async def create_payment_session(
        self, auth_user_id: int, payment_request: PaymentCreateSchema
    ) -> PaymentSessionReadSchema:
        """
        Create a checkout session.
        """

    @abstractmethod
    async def handle_webhook(self, payload: bytes, headers: dict) -> None:
        """
        Verify webhook event.
        """

    @abstractmethod
    async def refund_payment(
        self, auth_user_id: int, refund_request: RefundCreateSchema
    ) -> RefundStatusReadSchema:
        """
        Process a refund.
        """

    @abstractmethod
    async def list_all_payments(
        self,
        user_id: Optional[int] = None,
        status: Optional[PaymentStatusEnum] = None,
        date: Optional[datetime] = None,
    ) -> list[PaymentReadSchema]:
        """
        List all payments with optional filters by user, status, date
        """

    @abstractmethod
    async def get_payment_status(self, ext_session_id: str) -> PaymentStatusReadSchema:
        """
        Get the payment status
        """
