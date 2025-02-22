import pytest
from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from bot.database.engine import create_db, drop_db, Base
from bot.database.models import Category, Product, User, Cart, Banner


# Фикстура для тестовой БД
@pytest.fixture(autouse=True, scope="module")
async def test_db_setup():
    # Используем временную SQLite базу в памяти
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    test_session_maker = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    # Переопределяем глобальные зависимости
    global engine, session_maker
    engine = test_engine
    session_maker = test_session_maker

    yield

    await engine.dispose()


@pytest.mark.asyncio
async def test_create_drop_tables():
    """Тест создания и удаления таблиц"""
    async with engine.begin() as conn:
        inspector = inspect(conn)
        tables = inspector.get_table_names()
        assert not tables  # Проверяем пустую БД

        # Создаем таблицы
        await conn.run_sync(Base.metadata.create_all)
        tables = inspector.get_table_names()
        expected_tables = [
            'user', 'category', 'product',
            'cart', 'order', 'order_item', 'banner'
        ]
        for table in expected_tables:
            assert table in tables

        # Удаляем таблицы
        await conn.run_sync(Base.metadata.drop_all)
        assert not inspector.get_table_names()


@pytest.mark.asyncio
async def test_initial_data_population():
    """Тест заполнения начальных данных"""
    await create_db()

    async with session_maker() as session:
        # Проверяем категории
        categories = await session.execute(select(Category))
        assert categories.scalars().all()

        # Проверяем баннеры
        banners = await session.execute(select(Banner))
        assert banners.scalars().all()

    await drop_db()


@pytest.mark.asyncio
async def test_engine_lifecycle():
    """Тест жизненного цикла движка"""
    assert not engine.dispose()

    # Проверяем подключение
    async with engine.begin() as conn:
        await conn.execute(select(1))

    await engine.dispose()
    assert engine.dispose()


@pytest.mark.asyncio
async def test_session_management():
    """Тест работы с сессиями"""
    async with session_maker() as session:
        assert isinstance(session, AsyncSession)
        assert session.is_active

        # Проверяем базовые операции
        new_user = User(user_id=123)
        session.add(new_user)
        await session.commit()

        result = await session.execute(select(User))
        users = result.scalars().all()
        assert len(users) == 1
        assert users[0].user_id == 123


@pytest.mark.asyncio
async def test_relationships():
    """Тест связей между моделями"""
    async with session_maker() as session:
        # Создаем тестовые данные
        user = User(user_id=1)
        category = Category(name="Конфеты")
        product = Product(
            name="Мармеладные мишки",
            description="Вкусные мармеладные конфеты",
            price=150.0,
            image="bear.jpg",
            category=category
        )
        cart_item = Cart(user=user, product=product, quantity=5)

        session.add_all([user, category, product, cart_item])
        await session.commit()

        # Проверяем связи
        assert user.cart[0].product.name == "Мармеладные мишки"
        assert category.product[0].name == "Мармеладные мишки"