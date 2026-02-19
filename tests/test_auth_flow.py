import pytest

email = "test@test.com"
password = "StrongPassword123"


@pytest.mark.asyncio
async def test_full_auth_flow(client):

    register = await client.post(
        "/accounts/register/",
        json={
            "email": email,
            "password": password
        }
    )

    assert register.status_code == 200

    activate = await client.get(
        "/accounts/activate/",
        params={
            "email": email,
            "token": "fake-token"
        }
    )

    assert activate.status_code in [200, 400]

    login = await client.post(
        "/accounts/login/",
        json={
            "email": email,
            "password": password
        }
    )

    assert login.status_code == 201

    tokens = login.json()

    assert "access_token" in tokens
    assert "refresh_token" in tokens

    refresh_token = tokens["refresh_token"]

    refresh = await client.post(
        "/accounts/refresh/",
        json={
            "refresh_token": refresh_token
        }
    )

    assert refresh.status_code == 200
    assert "access_token" in refresh.json()

    logout = await client.post(
        "/accounts/logout/",
        json={
            "refresh_token": refresh_token
        }
    )

    assert logout.status_code == 200

    reset_req = await client.post(
        "/accounts/password-reset/request/",
        json={
            "email": email
        }
    )

    assert reset_req.status_code == 200
