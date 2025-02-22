import pytest
from datetime import datetime
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import (
    Base, Banner, Category, Product,
    User, Cart, Order, OrderItem
)


# Фикстура для тестовой сессии
@pytest.fixture(scope="function")
async def session(async_engine, async_session):
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        yield async_session
        await conn.run_sync(Base.metadata.drop_all)


# Тесты базовой модели
@pytest.mark.asyncio
async def test_base_model_timestamps(session: AsyncSession):
    # Проверка автоматического заполнения временных меток
    user = User(user_id=123)
    session.add(user)
    await session.commit()

    assert isinstance(user.created, datetime)
    assert isinstance(user.updated, datetime)
    assert user.created == user.updated

    # Проверка обновления метки updated
    user.first_name = "Test"
    await session.commit()
    assert user.updated > user.created


# Тесты модели Banner
@pytest.mark.asyncio
async def test_banner_model_constraints(session: AsyncSession):
    # Проверка уникальности имени
    banner1 = Banner(name="main_banner")
    session.add(banner1)
    await session.commit()

    banner2 = Banner(name="main_banner")
    session.add(banner2)
    with pytest.raises(IntegrityError):
        await session.commit()

    # Проверка ограничения длины имени
    banner3 = Banner(name="x" * 16)
    session.add(banner3)
    with pytest.raises(IntegrityError):
        await session.commit()


# Тесты модели Product
@pytest.mark.asyncio
async def test_product_relationships(session: AsyncSession):
    # Создание зависимых объектов
    category = Category(name="Electronics")
    product = Product(
        name="Smartphone",
        description="Test device",
        price=Decimal("999.99"),
        image="image.jpg",
        category=category
    )

    session.add_all([category, product])
    await session.commit()

    # Проверка связи категория-продукты
    stmt = select(Category).where(Category.name == "Electronics")
    result = await session.execute(stmt)
    category = result.scalar()
    assert len(category.product) == 1
    assert category.product[0].name == "Smartphone"


# Тесты модели User
@pytest.mark.asyncio
async def test_user_required_fields(session: AsyncSession):
    # Проверка обязательного поля user_id
    user = User()
    session.add(user)
    with pytest.raises(IntegrityError):
        await session.commit()


# Тесты модели Cart
@pytest.mark.asyncio
async def test_cart_relationships(session: AsyncSession):
    # Создание тестовых данных
    user = User(user_id=123)
    product = Product(
        name="Laptop",
        description="Test laptop",
        price=Decimal("1500.00"),
        image="laptop.jpg",
        category=Category(name="Computers")
    )
    cart = Cart(user=user, product=product, quantity=2)

    session.add_all([user, product, cart])
    await session.commit()

    # Проверка связей
    assert cart.user.user_id == 123
    assert cart.product.name == "Laptop"
    assert user.cart[0].quantity == 2


# Тесты модели Order
@pytest.mark.asyncio
async def test_order_defaults_and_relationships(session: AsyncSession):
    user = User(user_id=456)
    order = Order(user=user, total_price=Decimal("500.00"))

    session.add_all([user, order])
    await session.commit()

    # Проверка значений по умолчанию
    assert order.status == "pending"

    # Проверка связи с OrderItem
    order_item = OrderItem(
        order=order,
        product=Product(
            name="Tablet",
            description="Test tablet",
            price=Decimal("500.00"),
            image="tablet.jpg",
            category=Category(name="Gadgets")
        ),
        quantity=1,
        price=Decimal("500.00")
    )
    session.add(order_item)
    await session.commit()

    assert len(order.items) == 1
    assert order.items[0].product.name == "Tablet"


# Тесты каскадного удаления
@pytest.mark.asyncio
async def test_cascade_deletes(session: AsyncSession):
    # Создание цепочки зависимых объектов
    user = User(user_id=789)
    product = Product(
        name="Monitor",
        description="Test monitor",
        price=Decimal("300.00"),
        image="monitor.jpg",
        category=Category(name="Displays")
    )
    cart = Cart(user=user, product=product, quantity=1)
    order = Order(user=user, total_price=Decimal("300.00"))
    order_item = OrderItem(
        order=order,
        product=product,
        quantity=1,
        price=Decimal("300.00")
    )

    session.add_all([user, product, cart, order, order_item])
    await session.commit()

    # Удаление пользователя
    await session.delete(user)
    await session.commit()

    # Проверка каскадного удаления
    stmt = select(Cart).where(Cart.user_id == 789)
    result = await session.execute(stmt)
    assert result.scalar() is None

    # Проверка поведения ondelete для OrderItem
    stmt = select(OrderItem).where(OrderItem.order_id == order.id)
    result = await session.execute(stmt)
    assert result.scalar() is None


# Тест ограничений числовых полей
@pytest.mark.asyncio
async def test_numeric_constraints(session: AsyncSession):
    # Проверка точности Decimal
    with pytest.raises(IntegrityError):
        product = Product(
            name="Invalid Price",
            description="Test",
            price=Decimal("1000.123"),
            image="test.jpg",
            category=Category(name="Test")
        )
        session.add(product)
        await session.commit()


# Тест индексов и уникальных ограничений
@pytest.mark.asyncio
async def test_unique_constraints(session: AsyncSession):
    # Проверка уникальности user_id
    user1 = User(user_id=100)
    user2 = User(user_id=100)

    session.add_all([user1, user2])
    with pytest.raises(IntegrityError):
        await session.commit()