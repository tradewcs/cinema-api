import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from src.enums import OrderStatus, PaymentStatusEnum
from src.exceptions import (
    OrderNotFoundError,
    PaymentNotAllowed,
    PaymentSessionError,
    SignatureDoesNotExist,
    PaymentDoesNotExist,
)
from src.schemas.payments import PaymentCreateSchema
from tests.unit.payment.helpers import (
    make_fake_order,
    make_fake_payment,
    make_fake_stripe_session,
)


class TestWebhook:

    @pytest.mark.asyncio
    async def test_success_handler(
        self,
        stripe_processor,
        mock_order_repo,
        mock_payment_repo,
        mock_db,
    ):
        """Should change Order status to paid."""
        fake_order = make_fake_order(user_id=33)
        fake_event = MagicMock()
        fake_event.type = "checkout.session.completed"
        fake_session = make_fake_stripe_session()
        fake_session.metadata = {
            "order_id": fake_order.id,
            "user_id": fake_order.user_id,
        }
        fake_event.data.object = fake_session
        mock_order_repo.get_order_by_id.return_value = fake_order

        with patch.object(
            stripe_processor,
            "_get_verified_event",
            return_value=fake_event,
        ):
            payload = bytes()
            headers = {"stripe-signature": "test stripe-signature"}

            await stripe_processor.handle_webhook(
                payload=payload,
                headers=headers,
            )

        mock_order_repo.update_order_status.assert_awaited_once_with(
            fake_order.id, new_status=OrderStatus.PAID
        )
        mock_payment_repo.update.assert_awaited_once()
        mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_failed_handler(
        self, stripe_processor, mock_order_repo, mock_payment_repo, mock_db
    ):
        """Should change Payment status to CANCELLED."""
        fake_order = make_fake_order(user_id=33)
        fake_payment = make_fake_payment()
        fake_payment.status = PaymentStatusEnum.SUCCESSFUL
        mock_payment_repo.get_by_external_payment_id.return_value = fake_payment
        fake_event = MagicMock()
        fake_event.type = "checkout.session.async_payment_failed"
        fake_session = make_fake_stripe_session()
        fake_session.metadata = {
            "order_id": fake_order.id,
            "user_id": fake_order.user_id,
        }
        fake_event.data.object = fake_session
        mock_order_repo.get_order_by_id.return_value = fake_order

        with patch.object(
            stripe_processor,
            "_get_verified_event",
            return_value=fake_event,
        ):
            payload = bytes()
            headers = {"stripe-signature": "test stripe-signature"}

            await stripe_processor.handle_webhook(
                payload=payload,
                headers=headers,
            )

            mock_payment_repo.update.assert_awaited_once_with(
                fake_payment, status=PaymentStatusEnum.CANCELED
            )
            mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_refunded_handler(
        self, stripe_processor, mock_order_repo, mock_payment_repo, mock_db
    ):
        """Should change Order status to CANCELLED and payment status to REFUNDED."""
        fake_order = make_fake_order(user_id=33)
        fake_payment = make_fake_payment()
        fake_payment.status = PaymentStatusEnum.SUCCESSFUL

        # fake refund
        fake_refund = MagicMock()
        fake_refund.status = "succeeded"
        fake_refund.payment_intent = "fake intent"

        # fake event
        fake_event = MagicMock()
        fake_event.type = "refund.created"
        fake_event.data.object = fake_refund

        # fake session
        fake_session = make_fake_stripe_session()
        fake_session.data = [fake_session]
        fake_session.metadata.order_id = fake_order

        mock_order_repo.update_order_status.return_value = fake_order
        mock_payment_repo.get_by_external_payment_id.return_value = fake_payment
        mock_payment_repo.update.return_value = fake_payment

        with patch.object(
            stripe_processor,
            "_get_verified_event",
            return_value=fake_event,
        ):
            with patch(
                "src.services.stripe_payments.stripe.checkout.Session.list_async",
                new=AsyncMock(return_value=fake_session),
            ):
                payload = bytes()
                headers = {"stripe-signature": "test stripe-signature"}

                await stripe_processor.handle_webhook(
                    payload=payload,
                    headers=headers,
                )

                mock_order_repo.update_order_status.assert_awaited_once_with(
                    order_id=fake_order.id, new_status=OrderStatus.CANCELED
                )
                mock_payment_repo.update.assert_awaited_once_with(
                    fake_payment, status=PaymentStatusEnum.REFUNDED
                )
                mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_raises_signature_does_not_exist(self, stripe_processor):
        """When signature is not found SignatureDoesNotExist excepion raised"""

        with pytest.raises(SignatureDoesNotExist):
            await stripe_processor.handle_webhook(
                payload=bytes(),
                headers={},
            )

    @pytest.mark.asyncio
    async def test_raises_when_payment_does_not_exist(
        self, stripe_processor, mock_payment_repo
    ):
        """When payment to refund does not exist PaymentDoesNotExist exception raised"""
        fake_order = make_fake_order(user_id=33)
        fake_event = MagicMock()
        fake_event.type = "checkout.session.completed"
        fake_session = make_fake_stripe_session()
        fake_event.data.object = fake_session

        mock_payment_repo.get_by_external_payment_id.return_value = None

        with patch.object(
            stripe_processor,
            "_get_verified_event",
            return_value=fake_event,
        ):
            with pytest.raises(PaymentDoesNotExist):
                await stripe_processor.handle_webhook(
                    payload=bytes(),
                    headers={"stripe-signature": "fake signature"},
                )
