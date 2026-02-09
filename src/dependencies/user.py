from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.config import settings
from src.db.session import get_db
from src.models.accounts import User
from src.enums.accounts import UserGroupEnum

reusable_oauth2 = HTTPBearer()


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    auth: HTTPAuthorizationCredentials = Depends(reusable_oauth2)
) -> User:
    token = auth.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")  # твоє поле в токені
        if user_id is None:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

    result = await db.execute(
        select(User)
        .options(selectinload(User.group))
        .where(User.id == int(user_id))
    )
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
    if current_user.group.name not in [UserGroupEnum.ADMIN.value, UserGroupEnum.MODERATOR.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user