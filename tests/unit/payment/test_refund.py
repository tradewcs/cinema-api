from decimal import Decimal
import stripe

import pytest
from unittest.mock import patch, AsyncMock

from src.enums import OrderStatus, PaymentStatusEnum
from src.exceptions import (
    OrderNotFoundError,
    PaymentNotAllowed,
    PaymentSessionError,
    SessionDoesNotExistError,
    PaymentError,
)
from src.schemas.payments import PaymentCreateSchema, RefundCreateSchema
from tests.unit.payment.helpers import (
    make_fake_order,
    make_fake_payment,
    make_fake_stripe_session,
)


class TestRefund:

    @pytest.mark.asyncio
    async def test_refund_success(
        self,
        stripe_processor,
        mock_order_repo,
        mock_payment_repo,
        mock_payment_item_repo,
        mock_db,
    ):
        fake_user_id = 33
        fake_amount = Decimal(100)

        # payment

        fake_payment = make_fake_payment(amount=fake_amount)
        fake_payment.status = PaymentStatusEnum.SUCCESSFUL

        fake_session = make_fake_stripe_session()
        fake_session.payment_intent = "fake payment intent"
        fake_session.metadata = {
            "user_id": fake_user_id,
            "amount_paid": fake_amount,
            "payment_id": fake_payment.id,
        }
        fake_refund_request = RefundCreateSchema(
            session_id=fake_session.id, amount=fake_amount
        )
        mock_payment_repo.get_by_id.return_value = fake_payment

        with (
            patch(
                "src.services.stripe_payments.stripe.checkout.Session.retrieve_async",
                new=AsyncMock(return_value=fake_session),
            ),
            patch(
                "src.services.stripe_payments.stripe.Refund.create_async",
                new=AsyncMock(return_value={"status": "succeeded"}),
            ) as mock_refund,
        ):
            await stripe_processor.refund_payment(
                auth_user_id=fake_user_id, refund_request=fake_refund_request
            )

            mock_refund.assert_called_once_with(
                payment_intent=fake_session.payment_intent, amount=fake_amount * 100
            )

    @pytest.mark.asyncio
    async def test_raises_when_no_session_exists(
        self,
        stripe_processor,
        mock_order_repo,
        mock_payment_repo,
        mock_payment_item_repo,
        mock_db,
    ):
        """When fake session id is passed SessionDoesNotExistError exception raised"""
        fake_user_id = 33
        fake_refund_request = RefundCreateSchema(session_id="1", amount=Decimal(1))

        with pytest.raises(SessionDoesNotExistError):
            with patch(
                "src.services.stripe_payments.stripe.checkout.Session.retrieve_async",
                new=AsyncMock(return_value=None),
            ):
                await stripe_processor.refund_payment(
                    auth_user_id=fake_user_id, refund_request=fake_refund_request
                )

    @pytest.mark.asyncio
    async def test_raises_when_no_payment_intent_exists(
        self,
        stripe_processor,
        mock_order_repo,
        mock_payment_repo,
        mock_payment_item_repo,
        mock_db,
    ):
        """When session doesn't have payment intent SessionDoesNotExistError exception raised"""
        fake_user_id = 33
        fake_refund_request = RefundCreateSchema(session_id="1", amount=Decimal(1))
        fake_session = make_fake_stripe_session()
        fake_session.payment_intent = None

        with pytest.raises(SessionDoesNotExistError):
            with patch(
                "src.services.stripe_payments.stripe.checkout.Session.retrieve_async",
                new=AsyncMock(return_value=fake_session),
            ):
                await stripe_processor.refund_payment(
                    auth_user_id=fake_user_id, refund_request=fake_refund_request
                )

    @pytest.mark.asyncio
    async def test_raises_when_no_payment_is_already_refunded(
        self,
        stripe_processor,
        mock_order_repo,
        mock_payment_repo,
        mock_payment_item_repo,
        mock_db,
    ):
        """When payment is already refunded PaymentNotAllowed exception raised"""
        fake_user_id = 33
        fake_refund_request = RefundCreateSchema(session_id="1", amount=Decimal(100))
        fake_session = make_fake_stripe_session()
        fake_session.payment_intent = "some intent"
        fake_payment = make_fake_payment()
        fake_payment.status = PaymentStatusEnum.REFUNDED
        fake_session.metadata = {
            "payment_id": fake_payment.id,
            "amount_paid": fake_payment.amount,
            "user_id": fake_user_id,
        }
        mock_payment_repo.get_by_id.return_value = fake_payment
        with pytest.raises(PaymentNotAllowed):
            with patch(
                "src.services.stripe_payments.stripe.checkout.Session.retrieve_async",
                new=AsyncMock(return_value=fake_session),
            ):
                await stripe_processor.refund_payment(
                    auth_user_id=fake_user_id, refund_request=fake_refund_request
                )

    @pytest.mark.asyncio
    async def test_raises_when_amount_paid_mismatch(
        self,
        stripe_processor,
        mock_order_repo,
        mock_payment_repo,
        mock_payment_item_repo,
        mock_db,
    ):
        """When user amount mismatches payment amount PaymentNotAllowed exception raised"""

        fake_user_id = 33
        fake_refund_request = RefundCreateSchema(session_id="1", amount=Decimal(100))
        fake_session = make_fake_stripe_session()
        fake_session.payment_intent = "some intent"
        fake_payment = make_fake_payment(amount=Decimal(100))
        fake_payment.status = PaymentStatusEnum.SUCCESSFUL
        fake_session.metadata = {
            "payment_id": fake_payment.id,
            "amount_paid": fake_payment.amount + 1,
            "user_id": fake_user_id,
        }
        mock_payment_repo.get_by_id.return_value = fake_payment
        with pytest.raises(PaymentNotAllowed):
            with patch(
                "src.services.stripe_payments.stripe.checkout.Session.retrieve_async",
                new=AsyncMock(return_value=fake_session),
            ):
                await stripe_processor.refund_payment(
                    auth_user_id=fake_user_id, refund_request=fake_refund_request
                )

    @pytest.mark.asyncio
    async def test_raises_payment_error_if_stripe_error(
        self,
        stripe_processor,
        mock_order_repo,
        mock_payment_repo,
        mock_payment_item_repo,
        mock_db,
    ):
        fake_user_id = 33
        fake_amount = Decimal(100)

        # payment

        fake_payment = make_fake_payment(amount=fake_amount)
        fake_payment.status = PaymentStatusEnum.SUCCESSFUL

        fake_session = make_fake_stripe_session()
        fake_session.payment_intent = "fake payment intent"
        fake_session.metadata = {
            "user_id": fake_user_id,
            "amount_paid": fake_amount,
            "payment_id": fake_payment.id,
        }
        fake_refund_request = RefundCreateSchema(
            session_id=fake_session.id, amount=fake_amount
        )
        mock_payment_repo.get_by_id.return_value = fake_payment

        with (
            patch(
                "src.services.stripe_payments.stripe.checkout.Session.retrieve_async",
                new=AsyncMock(return_value=fake_session),
            ),
            patch(
                "src.services.stripe_payments.stripe.Refund.create_async",
                new=AsyncMock(
                    side_effect=stripe.error.StripeError("Stripe refund error")
                ),
            ),
        ):
            with pytest.raises(PaymentError):
                await stripe_processor.refund_payment(
                    auth_user_id=fake_user_id, refund_request=fake_refund_request
                )
