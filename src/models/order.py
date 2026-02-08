from datetime import datetime
from typing import List

from sqlalchemy import (
    ForeignKey,
    DateTime,
    func,
    Integer,
    DECIMAL,
    Enum
)
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.testing.schema import mapped_column

from src.db import Base
from src.enums import OrderStatus


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,

    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus),
        nullable=False,
        default=OrderStatus.PENDING
    )
    total_amount: Mapped[float | None] = mapped_column(
        DECIMAL(10, 2), nullable=True
    )

    user: Mapped["User"] = relationship(back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship(back_populates="order")

    payments: Mapped[list["Payment"]] = relationship(
        "Payment",
        back_populates="order",
        cascade="all, delete-orphan"
    )

    order_items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan"
    )

class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    movie_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("movies.id", ondelete="CASCADE"),
        nullable=False,
    )
    price_at_order: Mapped[float] = mapped_column(
        DECIMAL(10, 2), nullable=False
    )

    order: Mapped["Order"] = relationship(back_populates="items")

    movie: Mapped["Movie"] = relationship(back_populates="order_items")

    payment_items: Mapped[list["PaymentItem"]] = relationship(
        "PaymentItem",
        back_populates="order_item",
        cascade="all, delete-orphan"
    )
