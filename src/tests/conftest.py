import pytest_asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from src.db.session import SessionLocal


from httpx import AsyncClient, ASGITransport
from asgi_lifespan import LifespanManager

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


@pytest_asyncio.fixture
async def client():

    async with LifespanManager(app):

        transport = ASGITransport(app=app)

        async with AsyncClient(
            transport=transport,
            base_url="http://test"
        ) as ac:
            yield ac

@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session