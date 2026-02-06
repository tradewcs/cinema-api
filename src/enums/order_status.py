from enum import auto, Enum


class OrderStatus(str, Enum):
    PAID = auto()
    PENDING = auto()
    CANCELED = auto()