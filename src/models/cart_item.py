from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class CartItem(Base):
    __tablename__ = "cart_items"

    __table_args__ = (
        UniqueConstraint(
            "cart_id",
            "movie_id",
            name="uq_cart_item_cart_id_movie_id",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    cart_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("cart.id", ondelete="CASCADE"),
        nullable=False,
    )

    movie_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("movie.id", ondelete="RESTRICT"),
        nullable=False,
    )

    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    cart: Mapped["Cart"] = relationship(
        "Cart",
        back_populates="items",
    )

    movie: Mapped["Movie"] = relationship(
        "Movie",
        lazy="joined",
    )
