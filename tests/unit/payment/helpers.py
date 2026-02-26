from decimal import Decimal
from unittest.mock import MagicMock

from src.enums import OrderStatus


def make_fake_order(
    order_id=1,
    user_id=42,
    total_amount=Decimal("99.99"),
    status=OrderStatus.PENDING,
):
    order = MagicMock()
    order.id = order_id
    order.user_id = user_id
    order.total_amount = total_amount
    order.status = status
    order.items = []
    return order


def make_fake_payment(payment_id=10, amount=Decimal("99.99")):
    payment = MagicMock()
    payment.id = payment_id
    payment.amount = amount
    payment.external_payment_id = None  # will be set during the checkout
    return payment


def make_fake_stripe_session(session_id="cs_test_123", url="https://stripe.com/pay"):
    session = MagicMock()
    session.id = session_id
    session.url = url
    return session
