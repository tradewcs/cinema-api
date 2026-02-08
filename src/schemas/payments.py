from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict

from src.enums import PaymentStatusEnum


class PaymentReadItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    payment_id: int
    order_item_id: int
    price_at_payment: Decimal = Field(max_digits=10, decimal_places=2)


class PaymentReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    order_id: int
    status: PaymentStatusEnum = Field(default=PaymentStatusEnum.SUCCESSFUL)
    amount: Decimal = Field(max_digits=10, decimal_places=2)
    external_payment_id: str | None = None
    payment_items: list[PaymentReadItemSchema] = Field(default_factory=list)


class PaymentCreateSchema(BaseModel):
    user_id: int
    order_id: int
    amount: Decimal = Field(max_digits=10, decimal_places=2, gt=0)


class RefundCreateSchema(BaseModel):
    user_id: int
    session_id: str
    amount: Decimal = Field(max_digits=10, decimal_places=2, gt=0)


class RefundStatusReadSchema(BaseModel):
    message: str


class PaymentSessionReadSchema(BaseModel):
    session_id: str
    session_url: str


class PaymentStatusReadSchema(BaseModel):
    status: PaymentStatusEnum
