import pytest
from sqlalchemy import inspect, String, Text, Numeric, BigInteger, ForeignKey
from sqlalchemy.orm import relationship

from database.models import Base, Banner, Category, Product, User, Cart, Order, OrderItem


def test_base_model_columns():
    """Проверка полей created и updated в Base."""
    inspector = inspect(Base)
    # Проверяем, что все дочерние модели имеют created и updated
    for model in [Banner, Category, Product, User, Cart, Order, OrderItem]:
        assert 'created' in model.__table__.columns
        assert 'updated' in model.__table__.columns
        created_col = model.__table__.c.created
        updated_col = model.__table__.c.updated
        assert created_col.default.arg == 'now()'
        assert updated_col.default.arg == 'now()'
        assert updated_col.onupdate == 'now()'

def test_banner_model():
    """Проверка модели Banner."""
    assert Banner.__tablename__ == 'banner'
    columns = Banner.__table__.columns

    # Проверка полей
    assert columns['name'].type == String(15)
    assert columns['name'].unique
    assert columns['image'].type == String(150)
    assert columns['image'].nullable
    assert columns['description'].type == Text
    assert columns['description'].nullable
    assert columns['admin_link'].type == String(150)
    assert columns['admin_link'].nullable

def test_category_model():
    """Проверка модели Category."""
    assert Category.__tablename__ == 'category'
    columns = Category.__table__.columns

    assert columns['name'].type == String(150)
    assert not columns['name'].nullable

def test_product_model():
    """Проверка модели Product."""
    assert Product.__tablename__ == 'product'
    columns = Product.__table__.columns

    assert columns['name'].type == String(150)
    assert not columns['name'].nullable
    assert columns['description'].type == Text
    assert columns['price'].type == Numeric(5, 2)
    assert columns['image'].type == String(150)
    assert columns['category_id'].type == BigInteger  # Предположим, что тип соответствует ForeignKey

    # Проверка внешнего ключа
    fk = next(iter(columns['category_id'].foreign_keys))
    assert fk.column.table.name == 'category'
    assert fk.column.name == 'id'

    # Проверка отношения
    assert 'category' in Product.__mapper__.relationships

def test_user_model():
    """Проверка модели User."""
    assert User.__tablename__ == 'user'
    columns = User.__table__.columns

    assert columns['user_id'].type == BigInteger
    assert columns['user_id'].unique
    assert columns['first_name'].type == String(150)
    assert columns['first_name'].nullable
    assert columns['phone'].type == String(13)
    assert columns['phone'].nullable

def test_cart_model():
    """Проверка модели Cart."""
    assert Cart.__tablename__ == 'cart'
    columns = Cart.__table__.columns

    # Проверка внешних ключей
    user_fk = next(iter(columns['user_id'].foreign_keys))
    assert user_fk.column.table.name == 'user'
    assert user_fk.column.name == 'user_id'

    product_fk = next(iter(columns['product_id'].foreign_keys))
    assert product_fk.column.table.name == 'product'
    assert product_fk.column.name == 'id'

    # Проверка отношений
    assert 'user' in Cart.__mapper__.relationships
    assert 'product' in Cart.__mapper__.relationships

def test_order_model():
    """Проверка модели Order."""
    assert Order.__tablename__ == 'order'
    columns = Order.__table__.columns

    assert columns['total_price'].type == Numeric(10, 2)
    assert columns['status'].type == String(20)
    assert columns['status'].default.arg == 'pending'

    # Проверка внешнего ключа
    user_fk = next(iter(columns['user_id'].foreign_keys))
    assert user_fk.column.table.name == 'user'
    assert user_fk.column.name == 'user_id'

    # Проверка отношений
    assert 'user' in Order.__mapper__.relationships
    assert 'items' in Order.__mapper__.relationships

def test_order_item_model():
    """Проверка модели OrderItem."""
    assert OrderItem.__tablename__ == 'order_item'
    columns = OrderItem.__table__.columns

    assert columns['quantity'].nullable is False
    assert columns['price'].type == Numeric(10, 2)

    # Проверка внешних ключей
    order_fk = next(iter(columns['order_id'].foreign_keys))
    assert order_fk.column.table.name == 'order'
    assert order_fk.column.name == 'id'

    product_fk = next(iter(columns['product_id'].foreign_keys))
    assert product_fk.column.table.name == 'product'
    assert product_fk.column.name == 'id'

    # Проверка отношения
    assert 'product' in OrderItem.__mapper__.relationships