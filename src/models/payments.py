from datetime import datetime
from decimal import Decimal

from db import Base
from sqlalchemy import ForeignKey, Integer, DateTime, func
from enum import StrEnum, auto

from sqlalchemy.orm import Mapped, mapped_column, relationship


class PaymentStatusEnum(StrEnum):
    SUCCESSFUL = auto()
    CANCELED = auto()
    REFUNDED = auto()


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = (
        mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    )
    user: Mapped["User"] = relationship("User", back_populates="payments")
    order_id: Mapped[int] = (
        mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
    )
    order: Mapped["Order"] = relationship("Order", back_populates="payments")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    status: Mapped[PaymentStatusEnum] = mapped_column(
        PaymentStatusEnum, default=PaymentStatusEnum.SUCCESSFUL, nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(
        Decimal, precision=10, scale=2, nullable=False
    )
    external_payment_id: Mapped[int] = mapped_column(Integer, nullable=True)
    payment_items: Mapped[list["PaymentItem"]] = relationship(
        "PaymentItem", back_populates="payment", cascade="all, delete-orphan"
    )
