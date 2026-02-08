from fastapi import HTTPException, Request
from src.enums.accounts import UserGroupEnum


async def require_moderator(request: Request) -> None:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if user.group.name not in (UserGroupEnum.MODERATOR, UserGroupEnum.ADMIN):
        raise HTTPException(status_code=403, detail="Moderator privileges required")
