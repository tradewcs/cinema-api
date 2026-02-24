from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict

from src.enums import OrderStatus
from src.schemas.payments import PaymentSessionReadSchema


class OrderCreateSchema(BaseModel):
    user_id: int
    created_at: datetime
    status: OrderStatus = OrderStatus.PENDING
    total_amount: Decimal | None = Field(max_digits=10, decimal_places=2)

    model_config = ConfigDict(from_attributes=True)


class OrderReadSchema(BaseModel):
    id: int
    user_id: int
    created_at: datetime
    status: OrderStatus = OrderStatus.PENDING
    total_amount: Decimal | None = Field(max_digits=10, decimal_places=2)
    session_id: str | None = None
    session_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class OrderListSchema(BaseModel):
    id: int
    user_id: int
    created_at: datetime
    status: OrderStatus
    total_amount: Decimal | None

    model_config = ConfigDict(from_attributes=True)


class OrderItemCreateSchema(BaseModel):
    order_id: int
    movie_id: int
    price_at_order: Decimal = Field(max_digits=10, decimal_places=2)

    model_config = ConfigDict(from_attributes=True)


class OrderItemReadSchema(BaseModel):
    id: int
    order_id: int
    movie_id: int
    price_at_order: Decimal = Field(max_digits=10, decimal_places=2)
