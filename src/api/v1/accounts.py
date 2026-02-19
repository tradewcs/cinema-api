from fastapi import (
    APIRouter,
    Depends,
    status,
)

from src.dependencies.accounts import get_accounts_service
from services.accounts import AccountsService
from src.core.config import Settings
from src.dependencies.accounts import (
    get_jwt_auth_manager, get_settings,
)
from src.schemas.accounts import (
    UserRegistrationRequestSchema,
    UserRegistrationResponseSchema,
    MessageResponseSchema,
    PasswordResetRequestSchema,
    PasswordResetCompleteRequestSchema,
    UserLoginResponseSchema,
    UserLoginRequestSchema,
    TokenRefreshRequestSchema,
    TokenRefreshResponseSchema,
    ActivationResendRequestSchema
)
from src.security.interfaces import JWTAuthManagerInterface

router = APIRouter()


@router.post("/register/")
async def register_user(
    user_data: UserRegistrationRequestSchema,
    service: AccountsService = Depends(get_accounts_service),
):
    user = await service.register_user(
        email=user_data.email,
        password=user_data.password,
    )

    return UserRegistrationResponseSchema.model_validate(user)

@router.get("/activate/")
async def activate_account(
    email: str,
    token: str,
   service: AccountsService = Depends(get_accounts_service),
):

    await service.activate_account(
        email=email,
        token=token
    )

    return MessageResponseSchema(
        message="User account activated successfully."
    )

@router.post(
    "/password-reset/request/",
    response_model=MessageResponseSchema,
)
async def request_password_reset_token(
    data: PasswordResetRequestSchema,
    service: AccountsService = Depends(get_accounts_service),
):

    await service.request_password_reset(
        email=data.email
    )

    return MessageResponseSchema(
        message="If you are registered, you will receive an email with instructions."
    )


@router.post(
    "/password-reset/complete/",
    response_model=MessageResponseSchema,
)
async def reset_password(
    data: PasswordResetCompleteRequestSchema,
    service: AccountsService = Depends(get_accounts_service),
):

    await service.reset_password_complete(
        email=data.email,
        token=data.token,
        new_password=data.password,
    )

    return MessageResponseSchema(
        message="Password reset successfully."
    )

@router.post(
    "/login/",
    response_model=UserLoginResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def login_user(
    login_data: UserLoginRequestSchema,
    settings: Settings = Depends(get_settings),
    jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
    service: AccountsService = Depends(get_accounts_service),
) -> UserLoginResponseSchema:


    access_token, refresh_token = await service.login_user(
        email=login_data.email,
        password=login_data.password,
        jwt_manager=jwt_manager,
        refresh_ttl=settings.JWT_REFRESH_TTL,
    )

    return UserLoginResponseSchema(
        access_token=access_token,
        refresh_token=refresh_token,
    )

@router.post(
    "/refresh/",
    response_model=TokenRefreshResponseSchema,
)
async def refresh_access_token(
    token_data: TokenRefreshRequestSchema,
    jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
    service: AccountsService = Depends(get_accounts_service),
):

    new_access_token = await service.refresh_access_token(
        refresh_token=token_data.refresh_token,
        jwt_manager=jwt_manager
    )

    return TokenRefreshResponseSchema(
        access_token=new_access_token
    )

@router.post(
    "/logout/",
    response_model=MessageResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def logout_user(
    token_data: TokenRefreshRequestSchema,
    service: AccountsService = Depends(get_accounts_service),
) -> MessageResponseSchema:


    await service.logout_user(
        refresh_token=token_data.refresh_token
    )

    return MessageResponseSchema(
        message="Successfully logged out."
    )


@router.post(
    "/activate/resend/",
    response_model=MessageResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def resend_activation_email(
    data: ActivationResendRequestSchema,
    service: AccountsService = Depends(get_accounts_service),
) -> MessageResponseSchema:

    await service.resend_activation_email(
        data.email
    )

    return MessageResponseSchema(
        message="If your account exists and is not activated, a new activation link has been sent."
    )
