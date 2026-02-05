from enum import StrEnum, auto


class PaymentStatusEnum(StrEnum):
    SUCCESSFUL = auto()
    CANCELED = auto()
    REFUNDED = auto()
