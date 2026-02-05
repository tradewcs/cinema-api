from decimal import Decimal
from pydantic import BaseModel, Field

from models import PaymentStatusEnum


class PaymentCreateSchema(BaseModel):
    user_id: int
    order_id: int
    status: PaymentStatusEnum = Field(default=PaymentStatusEnum.SUCCESSFUL)
    amount: Decimal = Field(max_digits=10, decimal_places=2)
    external_payment_id: str | None = None
    payment_items: list["PaymentCreateItemSchema"] = Field(default_factory=list)
