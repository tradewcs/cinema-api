import pytest
from unittest.mock import patch, AsyncMock

from src.enums import OrderStatus
from src.exceptions import OrderNotFoundError, PaymentNotAllowed, PaymentSessionError
from src.schemas.payments import PaymentCreateSchema
from tests.unit.payment.helpers import (
    make_fake_order,
    make_fake_payment,
    make_fake_stripe_session,
)


class TestCreatePaymentSession:

    @pytest.mark.asyncio
    async def test_creates_session_successfully(
        self,
        stripe_processor,
        mock_order_repo,
        mock_payment_repo,
        mock_payment_item_repo,
        mock_db,
    ):
        """Should return a PaymentSessionReadSchema with session_id and session_url."""
        fake_order = make_fake_order()
        fake_payment = make_fake_payment()
        fake_stripe_session = make_fake_stripe_session()

        mock_order_repo.get_order_by_id.return_value = fake_order
        mock_payment_repo.create.return_value = fake_payment

        with patch(
            "src.services.stripe_payments.stripe.checkout.Session.create_async",
            new=AsyncMock(return_value=fake_stripe_session),
        ):
            result = await stripe_processor.create_payment_session(
                auth_user_id=42,
                payment_request=PaymentCreateSchema(order_id=1),
            )

        assert result.session_id == "cs_test_123"
        assert result.session_url == "https://stripe.com/pay"
        mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_sets_external_payment_id_on_payment(
        self, stripe_processor, mock_order_repo, mock_payment_repo, mock_db
    ):
        """The payment's external_payment_id should be set to the Stripe session id."""
        fake_order = make_fake_order()
        fake_payment = make_fake_payment()
        fake_stripe_session = make_fake_stripe_session(session_id="cs_test_abc")

        mock_order_repo.get_order_by_id.return_value = fake_order
        mock_payment_repo.create.return_value = fake_payment

        with patch(
            "src.services.stripe_payments.stripe.checkout.Session.create_async",
            new=AsyncMock(return_value=fake_stripe_session),
        ):
            await stripe_processor.create_payment_session(
                auth_user_id=42,
                payment_request=PaymentCreateSchema(order_id=1),
            )

        assert fake_payment.external_payment_id == "cs_test_abc"

    @pytest.mark.asyncio
    async def test_raises_when_order_not_found(self, stripe_processor, mock_order_repo):
        """When order is not found OrderNotFoundError excepion raised"""

        mock_order_repo.get_order_by_id.return_value = None

        with pytest.raises(OrderNotFoundError):
            await stripe_processor.create_payment_session(
                auth_user_id=42,
                payment_request=PaymentCreateSchema(order_id=999),
            )

    @pytest.mark.asyncio
    async def test_raises_when_order_belongs_to_different_user(
        self, stripe_processor, mock_order_repo
    ):
        """When order belongs to different user PaymentNotAllowed exception raised"""
        fake_order = make_fake_order(user_id=99)
        mock_order_repo.get_order_by_id.return_value = fake_order

        with pytest.raises(PaymentNotAllowed):
            await stripe_processor.create_payment_session(
                auth_user_id=42,
                payment_request=PaymentCreateSchema(order_id=1),
            )

    @pytest.mark.asyncio
    async def test_raises_when_order_is_not_pending(
        self, stripe_processor, mock_order_repo
    ):
        """When order doesn't have pending status PaymentNotAllowed exception raised"""

        fake_order = make_fake_order(status=OrderStatus.PAID)
        mock_order_repo.get_order_by_id.return_value = fake_order

        with pytest.raises(PaymentNotAllowed):
            await stripe_processor.create_payment_session(
                auth_user_id=42,
                payment_request=PaymentCreateSchema(order_id=1),
            )

    @pytest.mark.asyncio
    async def test_rolls_back_and_raises_on_stripe_error(
        self, stripe_processor, mock_order_repo, mock_payment_repo, mock_db
    ):
        """If Stripe raises, we should rollback and raise PaymentSessionError."""
        from sqlalchemy.exc import SQLAlchemyError

        fake_order = make_fake_order()
        fake_payment = make_fake_payment()

        mock_order_repo.get_order_by_id.return_value = fake_order
        mock_payment_repo.create.return_value = fake_payment

        with patch(
            "src.services.stripe_payments.stripe.checkout.Session.create_async",
            new=AsyncMock(side_effect=SQLAlchemyError("DB error")),
        ):
            with pytest.raises(PaymentSessionError):
                await stripe_processor.create_payment_session(
                    auth_user_id=42,
                    payment_request=PaymentCreateSchema(order_id=1),
                )

        mock_db.rollback.assert_awaited_once()
        mock_db.commit.assert_not_awaited()
