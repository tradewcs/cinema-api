from decimal import Decimal

from sqlalchemy.orm import Mapped, mapped_column, relationship

from db import Base
from sqlalchemy import ForeignKey, Integer


class PaymentItem(Base):
    __tablename__ = "payment_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payment_id: Mapped[int] = (
        mapped_column(ForeignKey("payments.id", ondelete="CASCADE"), nullable=False),
    )
    payment: Mapped["Payment"] = relationship("Payment", back_populates="payment_items")
    order_item_id: Mapped[int] = (
        mapped_column(ForeignKey("order_items.id", ondelete="CASCADE"), nullable=False),
    )
    order_item: Mapped["OrderItem"] = relationship(
        "OrderItem", back_populates="payment_items"
    )
    price_at_payment: Mapped[Decimal] = mapped_column(
        Decimal, precision=10, scale=2, nullable=False
    )
