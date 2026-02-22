from enum import auto, Enum


class OrderStatus(str, Enum):
    PAID = "paid"
    PENDING = "pending"
    CANCELED = "canceled"
