from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.db.session import get_db
from src.models.accounts import User
from src.enums.accounts import UserGroupEnum

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl="/api/v1/accounts/login"
)


async def get_current_user(
        db: AsyncSession = Depends(get_db),
        token: str = Depends(reusable_oauth2)
) -> User:
    """
    Decodes the JWT token and returns the current authenticated user.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return user


async def get_admin_user(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
) -> User:
    """
    Verifies if the current user has administrative or moderator privileges.
    """
    # Assuming User model has a relationship to UserGroup or group_id
    # This logic checks if the user's group name is ADMIN or MODERATOR
    if current_user.group.name not in [UserGroupEnum.ADMIN.value, UserGroupEnum.MODERATOR.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user