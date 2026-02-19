import pytest
from httpx import AsyncClient
from src.main import app
from src.notifications.interfaces import EmailSenderInterface
from src.dependencies.accounts import get_accounts_email_notificator


class FakeEmailSender(EmailSenderInterface):

    async def send_activation_email(self, *args, **kwargs):
        return

    async def send_activation_complete_email(self, *args, **kwargs):
        return

    async def send_password_reset_email(self, *args, **kwargs):
        return

    async def send_password_reset_complete_email(self, *args, **kwargs):
        return


def override_email_sender():
    return FakeEmailSender()


app.dependency_overrides[get_accounts_email_notificator] = override_email_sender


@pytest.fixture
async def client():
    async with AsyncClient(
        app=app,
        base_url="http://test"
    ) as ac:
        yield ac
