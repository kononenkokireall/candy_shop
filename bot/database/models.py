from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    BigInteger,
    func,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# Базовый класс для всех моделей SQLAlchemy.
# Здесь определены общие поля, которые будут присутствовать во всех таблицах.
class Base(DeclarativeBase):
    # Поле created хранит дату и время создания записи.
    # При создании записи в колонке автоматически будет установлено
    # текущее время.
    created: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    # Поле updated хранит дату и время последнего обновления записи.
    # Значение обновляется автоматически при каждом изменении записи.
    updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


# Модель Banner представляет таблицу "banner" в базе данных.
class Banner(Base):
    __tablename__ = "banner"
    # Определение индекса по полю name для ускорения поиска.
    __table_args__ = (Index("idx_banner_name", "name"),)

    # Первичный ключ таблицы, автоинкрементируемое целое число.
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # Название баннера. Ограничение unique гарантирует,
    # что каждое название будет уникальным.
    name: Mapped[str] = mapped_column(String(15), unique=True)
    # URL или путь к изображению баннера. Может быть пустым (nullable).
    image: Mapped[str] = mapped_column(String(150), nullable=True)
    # Описание баннера, может содержать большой текст.
    description: Mapped[str] = mapped_column(Text, nullable=True)
    # Ссылка для администратора, например,
    # для редактирования или просмотра деталей баннера.
    admin_link: Mapped[str] = mapped_column(String(150), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "image": self.image,
            "admin_link": self.admin_link
        }


# Модель Category представляет таблицу "category".
class Category(Base):
    __tablename__ = "category"
    __table_args__ = (Index("idx_category_name",
                            "name", unique=True),)

    # Первичный ключ категории.
    id: Mapped[int] = mapped_column(primary_key=True)
    # Название категории, обязательно для заполнения.
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    # Связь с продуктами, принадлежащими категории.
    # Back populates связывает это поле с полем category в модели Product.
    products: Mapped[list["Product"]] = relationship(back_populates="category")
    created_at: Mapped[datetime] = mapped_column(DateTime,
                                                 server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
        }


# Модель Product представляет таблицу "product".
class Product(Base):
    __tablename__ = "product"
    # Индекс по полю category_id для оптимизации поиска товаров по категории.
    __table_args__ = (Index("idx_product_category",
                            "category_id"),)

    # Первичный ключ товара.
    id: Mapped[int] = mapped_column(primary_key=True)
    # Название товара.
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    # Описание товара, может быть большим текстом.
    description: Mapped[str] = mapped_column(Text)
    # Цена товара с точностью до 2 знаков после запятой.
    price: Mapped[float] = mapped_column(Numeric(10, 2),
                                         nullable=False)
    # Путь к изображению товара.
    image: Mapped[str] = mapped_column(String(150))
    # Внешний ключ для связи с категорией товара.
    # При удалении категории связанные товары будут удалены (CASCADE).
    category_id: Mapped[int] = mapped_column(
        ForeignKey("category.id", ondelete="CASCADE"), nullable=False
    )

    # Определение связи с моделью Category.
    # Поле back_populates связывает с коллекцией products в модели Category.
    category: Mapped["Category"] = relationship(back_populates="products")
    # Связь с элементами заказа (OrderItem), где этот товар фигурирует.
    order_items: Mapped[list["OrderItem"]] = relationship(
        back_populates="product")
    # Связь с записями корзины, содержащими данный товар.
    carts: Mapped[list["Cart"]] = relationship(back_populates="product")


# Модель User представляет таблицу "user".
class User(Base):
    __tablename__ = "user"
    # Индекс по полю user_id для ускорения поиска пользователей.
    __table_args__ = (Index("ix_user_user_id", "user_id"),)

    # Добавить явное определение created/updated
    created: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Telegram User ID, используется как первичный ключ.
    user_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, unique=True, comment="Telegram User ID"
    )
    # Имя пользователя, может отсутствовать.
    first_name: Mapped[str] = mapped_column(String(150), nullable=False)
    # Фамилия пользователя, может отсутствовать.
    last_name: Mapped[str] = mapped_column(String(150), nullable=False)
    # Телефон пользователя.
    phone: Mapped[str] = mapped_column(String(13), nullable=True,
                                       server_default=None)

    # Связь с заказами, сделанными пользователем.
    # Cascade 'all, delete-orphan' означает,
    # что при удалении пользователя все связанные заказы будут удалены.
    # Lazy='selecting' обеспечивает оптимизированную
    # загрузку связанных объектов.
    orders: Mapped[list["Order"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="select"
    )
    # Связь с записями корзины, принадлежащими пользователю.
    carts: Mapped[list["Cart"]] = relationship(back_populates="user")


# Модель Cart представляет таблицу "cart" – записи корзины.
class Cart(Base):
    __tablename__ = "cart"
    # Ограничение UniqueConstraint обеспечивает,
    # что для каждой пары (user_id, product_id)
    # будет существовать не более одной записи в корзине.
    __table_args__ = (
        UniqueConstraint("user_id", "product_id",
                         name="uix_user_product"),
        Index("idx_cart_user", "user_id"),
        Index("idx_cart_product", "product_id"),
    )

    # Первичный ключ записи корзины.
    id: Mapped[int] = mapped_column(primary_key=True)
    # Внешний ключ для связи с пользователем.
    # При удалении пользователя запись корзины удаляется.
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("user.user_id", ondelete="CASCADE"),
        nullable=False
    )
    # Внешний ключ для связи с товаром.
    # При удалении товара запись корзины удаляется.
    product_id: Mapped[int] = mapped_column(
        ForeignKey("product.id", ondelete="CASCADE"), nullable=False
    )
    # Количество товара в корзине, по умолчанию 1.
    quantity: Mapped[int] = mapped_column(default=1)

    # Определение связи с пользователем.
    user: Mapped["User"] = relationship(back_populates="carts")
    # Определение связи с товаром.
    product: Mapped["Product"] = relationship(back_populates="carts")


# Модель Order представляет таблицу "orders" – заказы пользователей.
class Order(Base):
    __tablename__ = "orders"
    # Индекс для ускорения поиска заказов по статусу и пользователю.
    __table_args__ = (Index("idx_order_status_updated",
                            "user_id", "status"),)

    # Первичный ключ заказа.
    id: Mapped[int] = mapped_column(primary_key=True)
    # Внешний ключ для связи с пользователем, который сделал заказ.
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("user.user_id", ondelete="CASCADE"),
        nullable=False
    )
    # Общая стоимость заказа.
    total_price: Mapped[float] = mapped_column(Numeric(10, 2),
                                               nullable=False)
    # Статус заказа (например, pending, completed и т.д.).
    status: Mapped[str] = mapped_column(String(20), default="pending")

    # Определение связи с пользователем.
    user: Mapped["User"] = relationship(back_populates="orders")
    # Связь с элементами заказа. Cascade 'all, delete-orphan' гарантирует,
    # что при удалении заказа
    # все связанные элементы также удалятся.
    # Passive_deletes=True позволяет базе данных управлять удалением записей,
    # если установлен ON DELETE CASCADE.
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan",
        passive_deletes=True
    )
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "status": self.status,
            "items": [item.to_dict() for item in self.items],
            "created": self.created.isoformat()
        }



# Модель OrderItem представляет
# таблицу "order_item" – отдельные позиции заказа.
class OrderItem(Base):
    __tablename__ = "order_item"
    # Индекс для ускорения поиска по полю product_id.
    __table_args__ = (Index("idx_order_item_product",
                            "product_id"),)

    # Первичный ключ записи позиции заказа.
    id: Mapped[int] = mapped_column(primary_key=True)
    # Внешний ключ для связи с заказом.
    # При удалении заказа удаляются связанные позиции.
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False
    )
    # Внешний ключ для связи с товаром.
    # При удалении товара устанавливается значение NULL.
    product_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("product.id", ondelete="SET NULL"), nullable=True
    )
    # Количество единиц товара в заказе.
    quantity: Mapped[int] = mapped_column(nullable=False)
    # Цена товара в момент оформления заказа.
    price: Mapped[float] = mapped_column(Numeric(10, 2),
                                         nullable=False)

    # Определение связи с заказом.
    order: Mapped["Order"] = relationship(back_populates="items")
    # Определение связи с товаром.
    product: Mapped[Optional["Product"]] = relationship(
        back_populates="order_items")

    def to_dict(self):
        return {
            "product_id": self.product_id,
            "quantity": self.quantity,
            "price": float(self.price)

        }
