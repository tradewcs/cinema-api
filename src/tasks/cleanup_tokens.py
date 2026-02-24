from datetime import datetime, timezone
import asyncio

from sqlalchemy import delete
from celery import shared_task

from src.db.session import SessionLocal
from src.models.accounts import ActivationToken, PasswordResetToken


@shared_task(name="delete_expired_tokens")
def delete_expired_tokens():
    asyncio.run(_delete())


async def _delete():
    async with SessionLocal() as session:
        now = datetime.now(timezone.utc)

        await session.execute(
            delete(ActivationToken).where(
                ActivationToken.expires_at < now
            )
        )

        await session.execute(
            delete(PasswordResetToken).where(
                PasswordResetToken.expires_at < now
            )
        )

        await session.commit()
