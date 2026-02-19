from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.models.accounts import (
    User,
    UserGroup,
    UserGroupEnum,
    ActivationToken,
    PasswordResetToken,
    RefreshToken
)


class AccountsRepository:

    def __init__(self, db: AsyncSession):
        self.db = db


    async def get_user_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_user_by_id(self, user_id: int) -> User | None:
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def save_user(self, user: User) -> None:
        self.db.add(user)
        await self.db.flush()

    async def get_group_by_name(self, name: UserGroupEnum) -> UserGroup | None:
        stmt = select(UserGroup).where(UserGroup.name == name)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_activation_token(
        self,
        email: str,
        token: str,
    ) -> ActivationToken | None:

        stmt = (
            select(ActivationToken)
            .options(joinedload(ActivationToken.user))
            .join(User)
            .where(
                User.email == email,
                ActivationToken.token == token
            )
        )

        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_activation_token_by_user(
        self,
        user_id: int,
    ) -> ActivationToken | None:

        stmt = select(ActivationToken).where(
            ActivationToken.user_id == user_id
        )

        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def save_activation_token(
        self,
        token: ActivationToken,
    ) -> None:

        self.db.add(token)
        await self.db.flush()

    async def delete_activation_token(
        self,
        token: ActivationToken,
    ) -> None:

        await self.db.delete(token)

    async def get_password_reset_token(
        self,
        user_id: int,
        token: str,
    ) -> PasswordResetToken | None:

        stmt = select(PasswordResetToken).where(
            PasswordResetToken.user_id == user_id,
            PasswordResetToken.token == token
        )

        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def save_password_reset_token(
        self,
        token: PasswordResetToken,
    ) -> None:

        self.db.add(token)
        await self.db.flush()

    async def delete_password_reset_token(
        self,
        token: PasswordResetToken,
    ) -> None:

        await self.db.delete(token)

    async def get_refresh_token(
        self,
        token: str,
    ) -> RefreshToken | None:

        stmt = select(RefreshToken).where(
            RefreshToken.token == token
        )

        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def save_refresh_token(
        self,
        token: RefreshToken,
    ) -> None:

        self.db.add(token)
        await self.db.flush()

    async def delete_refresh_token(
        self,
        token: RefreshToken,
    ) -> None:

        await self.db.delete(token)

    async def commit(self) -> None:
        await self.db.commit()

    async def rollback(self) -> None:
        await self.db.rollback()

    async def get_active_user_by_email(
            self,
            email: str
    ) -> User | None:
        stmt = select(User).where(
            User.email == email,
            User.is_active == True
        )

        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def delete_password_reset_tokens_by_user(
            self,
            user_id: int
    ) -> None:
        await self.db.execute(
            delete(PasswordResetToken).where(
                PasswordResetToken.user_id == user_id
            )
        )

