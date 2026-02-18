from datetime import datetime, timezone
from typing import Annotated
from fastapi import Depends, status, HTTPException, APIRouter, Request, Query
from src.dependencies.services import PaymentServiceDep
from src.dependencies.user import get_current_user, get_admin_user
from src.enums import PaymentStatusEnum
from src.exceptions import (
    SessionDoesNotExistError,
    PaymentNotAllowed,
    PaymentAmountMismatch,
    PaymentSessionError,
    PaymentDoesNotExist,
    WebHookPaymentError,
    InvalidPayload,
    InvalidSignature,
    OrderNotFoundError,
    PaymentError,
    SignatureDoesNotExist,
)
from src.models import User

from src.schemas.payments import (
    PaymentCreateSchema,
    PaymentSessionReadSchema,
    RefundCreateSchema,
    PaymentStatusReadSchema,
    PaymentReadSchema,
    RefundStatusReadSchema,
)

router = APIRouter(tags=["payments"])


def validate_date(date: datetime | None = None) -> datetime | None:
    if date is None:
        return None

    if date >= datetime.now(timezone.utc):
        raise ValueError("date cannot be in the future")

    return date


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_session(
    auth_user: Annotated[User, Depends(get_current_user)],
    payment_data: PaymentCreateSchema,
    stripe_service: PaymentServiceDep,
) -> PaymentSessionReadSchema:
    try:
        return await stripe_service.create_payment_session(auth_user.id, payment_data)
    except OrderNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order with id {payment_data.order_id} not found",
        )
    except (PaymentNotAllowed, PaymentAmountMismatch):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order with id {payment_data.order_id} is invalid",
        )
    except PaymentSessionError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Some error while creating payment session occurred",
        )


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def handle_webhook(
    request: Request,
    stripe_service: PaymentServiceDep,
) -> dict[str, str]:
    payload = await request.body()
    try:
        await stripe_service.handle_webhook(payload, dict(request.headers))
    except SignatureDoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing stripe-signature header",
        )
    except (
        PaymentDoesNotExist,
        SessionDoesNotExistError,
        PaymentDoesNotExist,
        InvalidPayload,
        InvalidSignature,
    ):
        raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail="Success",
        )
    except WebHookPaymentError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Missing stripe-signature header",
        )
    raise HTTPException(
        status_code=status.HTTP_200_OK,
        detail="Success",
    )


@router.get("", status_code=status.HTTP_200_OK)
async def list_all_payments(
    admin_user: Annotated[User, Depends(get_admin_user)],  # noqa
    stripe_service: PaymentServiceDep,
    user_id: Annotated[int | None, Query(gt=0)] = None,
    status: PaymentStatusEnum | None = None,
    date: Annotated[datetime | None, Depends(validate_date)] = None,
) -> list[PaymentReadSchema]:
    return await stripe_service.list_all_payments(
        user_id=user_id,
        status=status,
        date=date,
    )


@router.post("/refund", status_code=status.HTTP_201_CREATED)
async def handle_refund(
    auth_user: Annotated[User, Depends(get_current_user)],
    refund_data: RefundCreateSchema,
    stripe_service: PaymentServiceDep,
) -> RefundStatusReadSchema:
    try:
        return await stripe_service.refund_payment(auth_user.id, refund_data)
    except (SessionDoesNotExistError, PaymentNotAllowed):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No session found by the id {refund_data.session_id}",
        )
    except PaymentError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Some error occurred while refunding",
        )


@router.get("/success", status_code=status.HTTP_200_OK)
async def payment_success(
    ext_session_id: str,
    stripe_service: PaymentServiceDep,
) -> PaymentStatusReadSchema:
    try:
        return await stripe_service.get_payment_status(ext_session_id)
    except SessionDoesNotExistError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No session found by the id {ext_session_id}",
        )


@router.get("/cancel", status_code=status.HTTP_200_OK)
async def payment_cancel(
    ext_session_id: str,
    stripe_service: PaymentServiceDep,
) -> PaymentStatusReadSchema:
    try:
        return await stripe_service.get_payment_status(ext_session_id)
    except SessionDoesNotExistError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No session found by the id{ext_session_id}",
        )
