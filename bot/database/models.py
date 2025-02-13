from sqlalchemy import (
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    BigInteger,
    func
)

from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship
)

# Базовый класс для всех моделей. Определяет стандартные столбцы `created` и `updated`.
class Base(DeclarativeBase):
    """
    Базовый класс для всех моделей. Включает автоматическое добавление следующих столбцов:
    - created: Дата/время создания записи (устанавливается автоматически)
    - updated: Дата/время последнего изменения записи (обновляется автоматически)
    """
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


# Модель для баннеров (информационные страницы)
class Banner(Base):
    """
    Таблица `banner` для хранения информационных баннеров/страниц.
    Поля:
    - id: Автоинкрементный ID записи
    - name: Название баннера (уникальное, не более 15 символов)
    - image: URL изображения для баннера (опционально)
    - description: Описание баннера (опционально)
    - admin_link: Ссылка для администраторов для управления баннером (опционально)
    """
    __tablename__ = 'banner'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(15), unique=True)
    image: Mapped[str] = mapped_column(String(150), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    admin_link: Mapped[str] = mapped_column(String(150), nullable=True)


# Модель для категорий товаров
class Category(Base):
    """
    Таблица `category` для хранения категорий товаров.
    Поля:
    - id: Автоинкрементный ID записи
    - name: Название категории (обязательно)
    """
    __tablename__ = 'category'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)


# Модель для товаров
class Product(Base):
    """
    Таблица `product` для хранения информации о товарах.
    Поля:
    - id: Автоинкрементный ID записи
    - name: Название товара (обязательно)
    - description: Подробное описание товара
    - price: Цена товара (с точностью до 2 знаков)
    - image: URL изображения товара
    - category_id: ID категории, к которой относится товар (внешний ключ)

    Связи:
    - category: Отношение с категорией (многие к одному)
    """
    __tablename__ = 'product'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text)
    price: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    image: Mapped[str] = mapped_column(String(150))
    category_id: Mapped[int] = mapped_column(ForeignKey('category.id',
                                                        ondelete='CASCADE'), nullable=False)

    category: Mapped['Category'] = relationship(backref='product')


# Модель для пользователей
class User(Base):
    """
    Таблица `user` для хранения информации о пользователях.
    Поля:
    - id: Автоинкрементный ID записи
    - user_id: Уникальный ID пользователя (например, внешний источник, Telegram ID)
    - first_name: Имя пользователя (опционально)
    - last_name: Фамилия пользователя (опционально)
    - phone: Номер телефона (опционально)
    """
    __tablename__ = 'user'

    id: Mapped[int] = mapped_column( primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    first_name: Mapped[str] = mapped_column(String(150), nullable=True)
    last_name: Mapped[str] = mapped_column(String(150), nullable=True)
    phone: Mapped[str] = mapped_column(String(13), nullable=True)


# Модель для корзины (связь пользователя с выбранными товарами)
class Cart(Base):
    """
    Таблица `cart` для хранения содержимого корзины пользователя.
    Поля:
    - id: Автоинкрементный ID записи
    - user_id: ID пользователя (внешний ключ)
    - product_id: ID товара (внешний ключ)
    - quantity: Количество товара в корзине

    Связи:
    - user: Отношение многие к одному с таблицей User
    - product: Отношение многие к одному с таблицей Product
    """
    __tablename__ = 'cart'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('user.user_id',
                                                                ondelete='CASCADE'), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey('product.id', ondelete='CASCADE'), nullable=False)
    quantity: Mapped[int]
    user: Mapped['User'] = relationship(backref='cart')
    product: Mapped['Product'] = relationship(backref='cart')


# Модель для заказов
class Order(Base):
    """
    Таблица `order` для хранения информации о заказах.
    Поля:
    - id: Автоинкрементный ID записи
    - user_id: ID пользователя, сделавшего заказ (внешний ключ)
    - total_price: Общая стоимость заказа (с точностью до 2 знаков)
    - status: Статус заказа (по умолчанию 'pending')
    - address: Адрес доставки (опционально)
    - phone: Контактный номер телефона (опционально)

    Связи:
    - user: Отношение многие к одному с таблицей User
    - items: Отношение один ко многим с таблицей OrderItem
    """
    __tablename__ = 'order'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('user.user_id',
                                                                ondelete='CASCADE'), nullable=False)
    # Общая сумма заказа
    total_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    # Статус заказа
    status: Mapped[str] = mapped_column(String(20), default='pending')
    # Адрес доставки
    address: Mapped[str] = mapped_column(String(200), nullable=True)
    # Контактный телефон
    phone: Mapped[str] = mapped_column(String(13), nullable=True)

    # Связи
    user: Mapped['User'] = relationship(backref='orders')
    items: Mapped[list['OrderItem']] = relationship(backref='order', cascade='all, delete')


# Модель для позиций внутри заказов
class OrderItem(Base):
    """
    Таблица `order_item` для информации о позициях в заказах (связь заказ-товар).
    Поля:
    - id: Автоинкрементный ID записи
    - order_id: ID заказа (внешний ключ)
    - product_id: ID товара (внешний ключ)
    - quantity: Количество товара в заказе
    - price: Цена товара на момент оформления заказа

    Связи:
    - product: Отношение многие к одному с таблицей Product
    """
    __tablename__ = 'order_item'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey('order.id', ondelete='CASCADE'), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey('product.id', ondelete='CASCADE'), nullable=False)
    # Количество товара
    quantity: Mapped[int] = mapped_column(nullable=False)
    # Цена на момент покупки
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    product: Mapped['Product'] = relationship(backref='order_items')
