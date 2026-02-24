from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict

from src.enums import PaymentStatusEnum, OrderStatus
from src.schemas import OrderItemReadSchema


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
    created_at: datetime
    external_payment_id: str | None = None
    payment_items: list[PaymentReadItemSchema] = Field(default_factory=list)


class PaymentCreateSchema(BaseModel):
    order_id: int


class RefundCreateSchema(BaseModel):
    session_id: str
    amount: Decimal = Field(max_digits=10, decimal_places=2, gt=0)


class RefundStatusReadSchema(BaseModel):
    message: str


class PaymentSessionReadSchema(BaseModel):
    session_id: str
    session_url: str


class PaymentStatusReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    order_id: int
    order_status: OrderStatus
    order_items: list[OrderItemReadSchema]
    paid_at: datetime
    amount: Decimal = Field(max_digits=10, decimal_places=2, gt=0)
