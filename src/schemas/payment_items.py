from decimal import Decimal
from pydantic import BaseModel, Field


class PaymentCreateItemSchema(BaseModel):
    payment_id: int
    order_item_id: int
    price_at_payment: Decimal = Field(max_digits=10, decimal_places=2)
