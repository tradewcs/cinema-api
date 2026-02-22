import pytest
from sqlalchemy import select
from src.models import User
import uuid


@pytest.mark.asyncio
async def test_full_auth_flow(client, db_session):

    test_email = f"test_{uuid.uuid4()}@example.com"
    test_password = f"Test{uuid.uuid4()}%"

    # ✅ Register
    register = await client.post(
        "/api/v1/accounts/register/",
        json={"email": test_email, "password": test_password}
    )
    assert register.status_code == 200

    # ✅ Activate manually
    result = await db_session.execute(
        select(User).where(User.email == test_email)
    )
    user = result.scalar_one()

    user.is_active = True
    await db_session.commit()

    # ✅ Login
    login = await client.post(
        "/api/v1/accounts/login/",
        json={"email": test_email, "password": test_password}
    )
    assert login.status_code == 201

    tokens = login.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    refresh_token = tokens["refresh_token"]

    # ✅ Refresh
    refresh = await client.post(
        "/api/v1/accounts/refresh/",
        json={"refresh_token": refresh_token}
    )
    assert refresh.status_code == 200
    assert "access_token" in refresh.json()

    # ✅ Logout
    logout = await client.post(
        "/api/v1/accounts/logout/",
        json={"refresh_token": refresh_token}
    )
    assert logout.status_code == 200

    # ✅ Password reset request
    reset_req = await client.post(
        "/api/v1/accounts/password-reset/request/",
        json={"email": test_email}
    )
    assert reset_req.status_code == 200