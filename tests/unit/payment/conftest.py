import pytest
from unittest.mock import AsyncMock

from src.services.stripe_payments import StripePaymentProcessor


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def mock_payment_repo():
    return AsyncMock()


@pytest.fixture
def mock_payment_item_repo():
    return AsyncMock()


@pytest.fixture
def mock_order_repo():
    return AsyncMock()


@pytest.fixture
def stripe_processor(
    mock_db, mock_payment_repo, mock_payment_item_repo, mock_order_repo
):
    return StripePaymentProcessor(
        db=mock_db,
        payment_repo=mock_payment_repo,
        payment_item_repo=mock_payment_item_repo,
        order_repo=mock_order_repo,
    )
