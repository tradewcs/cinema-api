from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone
from typing import cast
from src.exceptions.security import BaseSecurityError
from sqlalchemy.ext.asyncio import AsyncSession
from src.security.interfaces import JWTAuthManagerInterface
from src.models.accounts import (
    User,
    UserGroupEnum,
    ActivationToken, RefreshToken, PasswordResetToken
)
from src.notifications.interfaces import EmailSenderInterface
from src.repositories.accounts import AccountsRepository
from src.core.config import settings


class AccountsService:

    def __init__(
        self,
        repo: AccountsRepository,
        email_sender: EmailSenderInterface,
    ):
        self.repo = repo
        self.email_sender = email_sender

    async def register_user(
        self,
        email: str,
        password: str,
    ) -> User:

        existing_user = await self.repo.get_user_by_email(email)

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A user with this email {email} already exists."
            )

        group = await self.repo.get_group_by_name(UserGroupEnum.USER)

        if not group:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Default user group not found."
            )

        try:

            new_user = User.create(
                email=email,
                raw_password=password,
                group_id=group.id,
            )

            await self.repo.save_user(new_user)

            activation_token = ActivationToken(
                user_id=new_user.id
            )

            await self.repo.save_activation_token(
                activation_token
            )

            await self.repo.commit()

        except SQLAlchemyError as e:
            await self.repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred during user creation."
            ) from e

        activation_link = (
            f"{settings.BASE_URL}/accounts/activate"
            f"?email={new_user.email}&token={activation_token.token}"
        )

        await self.email_sender.send_activation_email(
            new_user.email,
            activation_link
        )

        return new_user


    async def activate_account(
            self,
            email: str,
            token: str,
    ) -> None:

        token_record = await self.repo.get_activation_token(
            email=email,
            token=token
        )

        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired activation token."
            )

        expires_at = cast(
            datetime,
            token_record.expires_at
        ).replace(tzinfo=timezone.utc)

        if expires_at < datetime.now(timezone.utc):
            await self.repo.delete_activation_token(token_record)
            await self.repo.commit()

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired activation token."
            )

        user = token_record.user

        if user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User account is already active."
            )

        user.is_active = True

        await self.repo.save_user(user)
        await self.repo.delete_activation_token(token_record)
        await self.repo.commit()

        login_link = f"{settings.BASE_URL}/accounts/login/"

        await self.email_sender.send_activation_complete_email(
            email,
            login_link
        )


    async def login_user(
            self,
            email: str,
            password: str,
            jwt_manager: JWTAuthManagerInterface,
            refresh_ttl: int,
    ) -> tuple[str, str]:

        user = await self.repo.get_user_by_email(email)

        if not user or not user.verify_password(password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is not activated.",
            )

        jwt_refresh_token = jwt_manager.create_refresh_token(
            {"user_id": user.id}
        )

        try:
            refresh_token = RefreshToken.create(
                user_id=user.id,
                days_valid=refresh_ttl,
                token=jwt_refresh_token
            )

            await self.repo.save_refresh_token(refresh_token)
            await self.repo.commit()

        except SQLAlchemyError:
            await self.repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while processing the request.",
            )

        jwt_access_token = jwt_manager.create_access_token(
            {"user_id": user.id}
        )

        return jwt_access_token, jwt_refresh_token


    async def logout_user(
            self,
            refresh_token: str,
    ) -> None:

        token_record = await self.repo.get_refresh_token(
            refresh_token
        )

        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not found.",
            )

        try:
            await self.repo.delete_refresh_token(token_record)
            await self.repo.commit()

        except SQLAlchemyError:
            await self.repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while processing the request.",
            )


    async def request_password_reset(
            self,
            email: str,
    ) -> None:

        user = await self.repo.get_active_user_by_email(email)

        if not user:
            return

        try:
            await self.repo.delete_password_reset_tokens_by_user(
                user.id
            )

            reset_token = PasswordResetToken(
                user_id=user.id
            )

            await self.repo.save_password_reset_token(
                reset_token
            )

            await self.repo.commit()

        except SQLAlchemyError:
            await self.repo.rollback()
            return

        reset_link = (
            f"{settings.BASE_URL}/accounts/reset-password/complete"
            f"?token={reset_token.token}"
        )

        await self.email_sender.send_password_reset_email(
            email,
            reset_link
        )


    async def reset_password_complete(
            self,
            email: str,
            token: str,
            new_password: str,
    ) -> None:

        user = await self.repo.get_active_user_by_email(email)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email or token."
            )

        token_record = await self.repo.get_password_reset_token(
            user.id,
            token
        )

        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email or token."
            )

        expires_at = cast(
            datetime,
            token_record.expires_at
        ).replace(tzinfo=timezone.utc)

        if expires_at < datetime.now(timezone.utc):
            await self.repo.delete_password_reset_token(token_record)
            await self.repo.commit()

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email or token."
            )

        try:
            user.password = new_password

            await self.repo.save_user(user)
            await self.repo.delete_password_reset_token(
                token_record
            )
            await self.repo.commit()

        except SQLAlchemyError:
            await self.repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while resetting the password."
            )

        login_link = f"{settings.BASE_URL}/accounts/login/"

        await self.email_sender.send_password_reset_complete_email(
            email,
            login_link
        )


    async def refresh_access_token(
            self,
            refresh_token: str,
            jwt_manager: JWTAuthManagerInterface,
    ) -> str:

        try:
            decoded_token = jwt_manager.decode_refresh_token(
                refresh_token
            )
            user_id = decoded_token.get("user_id")

        except BaseSecurityError as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error),
            )

        token_record = await self.repo.get_refresh_token(
            refresh_token
        )

        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not found.",
            )

        user = await self.repo.get_user_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        new_access_token = jwt_manager.create_access_token(
            {"user_id": user_id}
        )

        return new_access_token

    async def resend_activation_email(
            self,
            email: str,
    ) -> None:

        user = await self.repo.get_user_by_email(email)

        if not user or user.is_active:
            return

        old_token = await self.repo.get_activation_token_by_user(user.id)

        if old_token:
            await self.repo.delete_activation_token(old_token)

        new_token = ActivationToken(user_id=user.id)
        await self.repo.save_activation_token(new_token)
        await self.repo.commit()

        activation_link = (
            f"{settings.BASE_URL}/accounts/activate"
            f"?email={user.email}&token={new_token.token}"
        )

        await self.email_sender.send_activation_email(
            user.email,
            activation_link
        )
