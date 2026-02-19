from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.ext.asyncio.session import AsyncSession

from src.repositories.payments import PaymentRepository
from src.repositories.order import CrudOrder as OrderRepository
from src.repositories.payment_items import PaymentItemRepository
from src.enums import PaymentStatusEnum
from src.models import Order, Payment
from src.schemas.payments import (
    RefundStatusReadSchema,
    RefundCreateSchema,
    PaymentSessionReadSchema,
    PaymentCreateSchema,
    PaymentStatusReadSchema,
)
from src.services.interfaces import PaymentProcessorInterface
from typing import Optional, cast
from decimal import Decimal
from src.core import settings
import stripe
from src.enums.order_status import OrderStatus
from src.exceptions import *


class StripePaymentProcessor(PaymentProcessorInterface):
    def __init__(
        self,
        db: AsyncSession,
        payment_repo: PaymentRepository,
        payment_item_repo: PaymentItemRepository,
        order_repo: OrderRepository,
    ):
        self.db = db
        self.payment_repo = payment_repo
        self.payment_repo_item = payment_item_repo
        self.order_repo = order_repo
        self.webhook_secret = settings.STRIPE_WEBHOOK_SECRET

    async def _validate_order_amount(
        self, order: Order, payment_amount: Decimal
    ) -> Decimal:
        if order.total_amount != payment_amount:
            raise PaymentAmountMismatch(f"Order {order.id} has no items")
        return payment_amount

    async def _validate_order_for_user(self, order_id: int, user_id: int) -> Order:
        order = await self.order_repo.get_order_by_id(order_id)

        if order is None:
            raise OrderNotFoundError(f"Order {order_id} not found")

        if order.user_id != user_id:
            raise PaymentNotAllowed(
                f"Order {order_id} does not belong to user {user_id}"
            )

        if order.status != OrderStatus.PENDING:
            raise PaymentNotAllowed(f"Order {order_id} must be in PENDING status")

        return order

    async def create_payment_session(
        self, auth_user_id: int, payment_request: PaymentCreateSchema
    ) -> PaymentSessionReadSchema:

        order = await self._validate_order_for_user(
            order_id=payment_request.order_id, user_id=auth_user_id
        )

        validated_amount = await self._validate_order_amount(
            order, payment_request.amount
        )

        try:
            payment = await self.payment_repo.create(
                order_id=order.id, user_id=auth_user_id, amount=validated_amount
            )

            await self.payment_repo_item.create_from_order_items(
                payment_id=payment.id, order_items=order.items
            )

            success_url = f"{settings.BASE_URL}/payments/success?session_id={{CHECKOUT_SESSION_ID}}"
            cancel_url = f"{settings.BASE_URL}/payments/cancel?session_id={{CHECKOUT_SESSION_ID}}"
            session = await stripe.checkout.Session.create_async(
                mode="payment",
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": "usd",
                            "product_data": {
                                "name": "Purchase videos",
                            },
                            "unit_amount": int(payment_request.amount * 100),
                        },
                        "quantity": 1,
                    }
                ],
                metadata={
                    "order_id": order.id,
                    "user_id": auth_user_id,
                    "amount_paid": validated_amount,
                    "payment_id": payment.id,
                },
                success_url=success_url,
                cancel_url=cancel_url,
            )

            payment.external_payment_id = session.id

            await self.db.commit()

        except (SQLAlchemyError, IntegrityError):
            await self.db.rollback()
            raise PaymentSessionError("Error while creating payment session")

        return PaymentSessionReadSchema(session_id=session.id, session_url=session.url)

    def _get_verified_event(self, payload: bytes, sig_header: str) -> stripe.Event:
        try:
            return stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            raise InvalidPayload("Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise InvalidSignature("Invalid signature")

    async def _handle_successful_payment(
        self, payment: Payment, session: stripe.checkout.Session
    ) -> None:
        if payment.status == PaymentStatusEnum.SUCCESSFUL:
            return

        order_id = int(session.metadata.get("order_id"))
        user_id = int(session.metadata.get("user_id"))

        validated_order = await self._validate_order_for_user(
            order_id=order_id, user_id=user_id
        )
        new_payment_status = PaymentStatusEnum.SUCCESSFUL
        try:
            await self.order_repo.update_order_status(
                order_id, new_status=OrderStatus.PAID
            )
            await self.payment_repo.update(payment, status=new_payment_status)
            await self.db.commit()
        except (SQLAlchemyError, IntegrityError):
            await self.db.rollback()
            raise WebHookPaymentError("Error while processing webhook")

    async def _handle_failed_payment(
        self,
        payment: Payment,
    ) -> None:
        if payment.status == PaymentStatusEnum.CANCELED:
            return

        new_payment_status = PaymentStatusEnum.CANCELED
        try:
            await self.payment_repo.update(payment, status=new_payment_status)
            await self.db.commit()
        except (SQLAlchemyError, IntegrityError):
            await self.db.rollback()
            raise WebHookPaymentError("Error while processing webhook")

    async def _handle_refund_updated(self, refund: stripe.Refund) -> None:
        payment_intent = refund.payment_intent

        sessions = await stripe.checkout.Session.list_async(
            payment_intent=payment_intent.id, limit=1
        )

        if not sessions.data:
            raise SessionDoesNotExistError(
                "Session does not exist with given payment intent"
            )

        session = sessions.data[0]

        payment = await self.payment_repo.get_by_external_payment_id(session.id)

        if not payment:
            raise PaymentDoesNotExist("Payment does not exist")

        if refund.status == "succeeded":
            await self.payment_repo.update(payment, status=PaymentStatusEnum.REFUNDED)
            await self.db.commit()

    async def handle_webhook(self, payload: bytes, headers: dict) -> None:
        sig_header = headers.get("stripe-signature")

        if not sig_header:
            raise SignatureDoesNotExist("Missing stripe-signature header")

        event = self._get_verified_event(payload=payload, sig_header=sig_header)

        if event.type in ("refund.updated", "refund.created"):
            refund = cast(stripe.Refund, event.data.object)
            await self._handle_refund_updated(refund)
            return

        session = cast(stripe.checkout.Session, event.data.object)

        stripe_session_id = session.id

        payment = await self.payment_repo.get_by_external_payment_id(stripe_session_id)
        if not payment:
            raise PaymentDoesNotExist("Payment does not exist")

        if event.type == "checkout.session.completed":
            await self._handle_successful_payment(payment=payment, session=session)

        elif event.type in (
            "checkout.session.expired",
            "checkout.session.async_payment_failed",
        ):
            await self._handle_failed_payment(payment=payment)

    async def refund_payment(
        self,
        auth_user_id: int,
        refund_request: RefundCreateSchema,
    ) -> RefundStatusReadSchema:

        # get the payment intent
        session = await stripe.checkout.Session.retrieve_async(
            refund_request.session_id
        )
        if not session:
            raise SessionDoesNotExistError(
                f"No session exist with id {refund_request.session_id}"
            )

        # validate the payment intent
        user_payment_intent = session.payment_intent
        if not user_payment_intent:
            raise SessionDoesNotExistError("No payment intent found for this session")

        # validate the user to refund
        if session.metadata.get("user_id") != auth_user_id:
            raise PaymentNotAllowed("Refund not allowed")

        amount_in_cents = int(refund_request.amount * 100)

        # validate the refund amount
        amount_paid = Decimal(session.metadata.get("amount_paid"))
        if amount_paid != refund_request.amount:
            raise PaymentNotAllowed("Refund not allowed")

        # validate if payment is already refunded
        payment_id = int(session.metadata.get("payment_id"))
        payment = await self.payment_repo.get_by_id(payment_id=payment_id)

        if payment.status == PaymentStatusEnum.REFUNDED:
            raise PaymentNotAllowed("Refund not allowed")

        try:
            await stripe.Refund.create_async(
                payment_intent=user_payment_intent, amount=amount_in_cents
            )
            return RefundStatusReadSchema(message="Success")
        except stripe.error.StripeError as e:
            raise PaymentError("Some error occurred while refunding")

    async def list_all_payments(
        self,
        user_id: Optional[int] = None,
        status: Optional[PaymentStatusEnum] = None,
        date: Optional[datetime] = None,
    ) -> list[Payment]:
        return await self.payment_repo.get_all(
            user_id=user_id, status=status, date=date
        )

    async def get_payment_status(self, ext_session_id: str) -> PaymentStatusReadSchema:
        payment = await self.payment_repo.get_by_external_payment_id(
            external_payment_id=ext_session_id
        )
        if not payment or not payment.external_payment_id:
            raise SessionDoesNotExistError(
                f"Session does not exist with {ext_session_id}"
            )
        return PaymentStatusReadSchema(status=payment.status)
