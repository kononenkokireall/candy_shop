from __future__ import annotations

"""SQLAlchemy models (second‑iteration).

Изменения к версии 2:
1. **Деньги** — `Decimal` + `Numeric(10, 2)` (осталось с v1).
2. **Enum OrderStatus** — в схеме и Python (осталось с v1).
3. **CHECK‑констрейнты** — цена товара ≥ 0, цена позиции ≥ 0, сумма заказа ≥ 0.
4. **Копия `product_name` в OrderItem** — остаётся даже если товар удалён.
5. **Индекс `order_id` в OrderItem** — быстрый доступ «все позиции заказа».
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func, Integer,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    """Базовая модель со штампами времени."""

    created: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


# ---------------------------------------------------------------------------
#                B A N N E R
# ---------------------------------------------------------------------------
class Banner(Base):
    __tablename__ = "banner"
    __table_args__ = (
        Index("idx_banner_name", "name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(15), unique=True)
    image: Mapped[Optional[str]] = mapped_column(String(150))
    description: Mapped[Optional[str]] = mapped_column(Text)
    admin_link: Mapped[Optional[str]] = mapped_column(String(150))


# ---------------------------------------------------------------------------
#                C A T E G O R Y
# ---------------------------------------------------------------------------
class Category(Base):
    __tablename__ = "category"
    __table_args__ = (
        Index("idx_category_name", "name", unique=True),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)

    products: Mapped[list["Product"]] = relationship(back_populates="category")


# ---------------------------------------------------------------------------
#                P R O D U C T
# ---------------------------------------------------------------------------
class Product(Base):
    __tablename__ = "product"
    __table_args__ = (
        Index("idx_product_category", "category_id"),
        CheckConstraint("price >= 0", name="chk_product_price_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2),
                                           nullable=False)
    image: Mapped[str] = mapped_column(String(150))
    category_id: Mapped[int] = mapped_column(
        ForeignKey("category.id", ondelete="CASCADE"), nullable=False
    )
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0,
                                       server_default="0")

    category: Mapped["Category"] = relationship(back_populates="products")
    order_items: Mapped[list["OrderItem"]] = relationship(
        back_populates="product")
    carts: Mapped[list["Cart"]] = relationship(back_populates="product")


# ---------------------------------------------------------------------------
#                U S E R
# ---------------------------------------------------------------------------
class User(Base):
    __tablename__ = "user"
    __table_args__ = (
        Index("ix_user_user_id", "user_id"),
    )

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(150))
    last_name: Mapped[str] = mapped_column(String(150))
    username: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(13))

    orders: Mapped[list["Order"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="select"
    )
    carts: Mapped[list["Cart"]] = relationship(back_populates="user")


# ---------------------------------------------------------------------------
#                C A R T
# ---------------------------------------------------------------------------
class Cart(Base):
    __tablename__ = "cart"
    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uix_user_product"),
        Index("idx_cart_user", "user_id"),
        Index("idx_cart_product", "product_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("user.user_id", ondelete="CASCADE"),
        nullable=False
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("product.id", ondelete="CASCADE"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(default=1)

    user: Mapped["User"] = relationship(back_populates="carts")
    product: Mapped["Product"] = relationship(back_populates="carts")


# ---------------------------------------------------------------------------
#                O R D E R   &   I T E M
# ---------------------------------------------------------------------------
class OrderStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    CANCELLED = "cancelled",
    CONFIRMED = "CONFIRMED"


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        Index("idx_order_status_updated", "user_id", "status"),
        CheckConstraint("total_price >= 0", name="chk_order_total_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("user.user_id", ondelete="CASCADE"),
        nullable=False
    )
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2),
                                                 nullable=False)
    status: Mapped[OrderStatus] = mapped_column(
        SAEnum(OrderStatus, name="order_status"), default=OrderStatus.PENDING
    )

    user: Mapped["User"] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan",
        passive_deletes=True
    )


class OrderItem(Base):
    __tablename__ = "order_item"
    __table_args__ = (
        Index("idx_order_item_order", "order_id"),
        Index("idx_order_item_product", "product_id"),
        CheckConstraint("price >= 0", name="chk_order_item_price_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("product.id", ondelete="SET NULL"), nullable=True
    )
    product_name: Mapped[Optional[str]] = mapped_column(
        String(150), nullable=True)  # snapshot name
    quantity: Mapped[int] = mapped_column(nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped[Optional["Product"]] = relationship(
        back_populates="order_items")

    # convenience: total for the line
    @property
    def line_total(self) -> Decimal:
        return self.price * self.quantity
