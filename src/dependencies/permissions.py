from fastapi import Request


async def require_moderator(request: Request) -> None:
    """
    TODO (future logic):
    - retrieve user from request.state.user or through JWT
    - check role MODERATOR/ADMIN
    - or 403
    """
    return None