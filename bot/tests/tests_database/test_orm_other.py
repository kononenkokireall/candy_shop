import logging

import pytest
from unittest.mock import AsyncMock, Mock, MagicMock, patch
from sqlalchemy import select, delete, update, desc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database.models import Product, OrderItem, Order
from database.orm_querys.orm_query_order import (
    orm_add_order_items,
    orm_delete_order,
    orm_get_order_details,
    orm_update_order_status,
    orm_get_user_orders,
    orm_add_order,
    orm_create_order
)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def test_orm_add_order_items_success():
    """Успешное добавление элементов заказа"""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.execute.return_value = AsyncMock(all=Mock(return_value=[(1,), (2,)]))

    items = [
        {"product_id": 1, "quantity": 2, "price": 100.0},
        {"product_id": 2, "quantity": 3, "price": 200.0}
    ]

    # Act
    await orm_add_order_items(mock_session, order_id=123, items=items)

    # Assert
    # Проверка вызова add_all с объектами OrderItem
    mock_session.add_all.assert_called_once()
    added_items = mock_session.add_all.call_args[0][0]
    assert len(added_items) == 2
    assert all(isinstance(item, OrderItem) for item in added_items)


async def test_orm_add_order_items_invalid_items_type():
    """Попытка добавить элементы не в формате списка"""
    with pytest.raises(ValueError, match="items должен быть списком"):
        await orm_add_order_items(AsyncMock(), order_id=123, items={"product_id": 1})


async def test_orm_add_order_items_missing_keys():
    """Элементы без обязательных ключей"""
    items = [{"product_id": 1, "quantity": 1}]  # Нет price
    with pytest.raises(ValueError, match="должен содержать product_id, quantity и price"):
        await orm_add_order_items(AsyncMock(), order_id=123, items=items)


async def test_orm_add_order_items_invalid_quantity():
    """Некорректное количество товара (quantity < 1)"""
    items = [{"product_id": 1, "quantity": 0, "price": 100.0}]
    with pytest.raises(ValueError, match="Некорректное количество"):
        await orm_add_order_items(AsyncMock(), order_id=123, items=items)


async def test_orm_add_order_items_invalid_price():
    """Отрицательная цена товара"""
    items = [{"product_id": 1, "quantity": 1, "price": -50.0}]
    with pytest.raises(ValueError, match="Некорректная цена"):
        await orm_add_order_items(AsyncMock(), order_id=123, items=items)


async def test_orm_add_order_items_missing_products():
    """Попытка добавить несуществующие товары"""
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.execute.return_value = AsyncMock(all=Mock(return_value=[(1,)]))  # Возвращает только ID=1

    items = [
        {"product_id": 1, "quantity": 1, "price": 100.0},
        {"product_id": 999, "quantity": 1, "price": 200.0}  # Несуществующий товар
    ]

    with pytest.raises(ValueError, match="Товары с ID {999} не найдены"):
        await orm_add_order_items(mock_session, order_id=123, items=items)


@pytest.mark.asyncio
async def test_orm_delete_order_success():
    """Успешное удаление существующего заказа"""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = AsyncMock()
    mock_result.rowcount = 1  # Заказ найден и удален
    mock_session.execute.return_value = mock_result

    order_id = 123

    # Act
    await orm_delete_order(mock_session, order_id)

    # Assert
    # Проверка формирования запроса
    expected_query = delete(Order).where(Order.id == order_id)
    mock_session.execute.assert_awaited_once_with(expected_query)

    # Проверка commit
    mock_session.commit.assert_awaited_once()

    # Проверка логов
    logger.info.assert_called_with(f"Заказ {order_id} успешно удален")


@pytest.mark.asyncio
async def test_orm_delete_order_not_found():
    """Попытка удаления несуществующего заказа"""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = AsyncMock()
    mock_result.rowcount = 0  # Заказ не найден
    mock_session.execute.return_value = mock_result

    order_id = 999

    # Act
    await orm_delete_order(mock_session, order_id)

    # Assert
    mock_session.commit.assert_awaited_once()
    logger.warning.assert_called_with(f"Заказ {order_id} не найден в базе")


@pytest.mark.asyncio
async def test_orm_delete_order_error():
    """Обработка ошибки при выполнении запроса"""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.execute.side_effect = Exception("Database error")

    order_id = 123

    # Act & Assert
    with pytest.raises(Exception, match="Database error"):
        await orm_delete_order(mock_session, order_id)

    # Проверка, что коммит не вызывался при ошибке
    mock_session.commit.assert_not_called()
    logger.error.assert_called_with("Ошибка при удалении заказа 123: Database error")


@pytest.mark.asyncio
async def test_successful_order_retrieval():
    # Создаем mock объекты
    mock_order = MagicMock(spec=Order)
    mock_order.id = 1
    mock_order.items = [MagicMock(spec=OrderItem, product=MagicMock(spec=Product))]

    # Мокаем результат запроса
    mock_result = MagicMock()
    mock_result.unique.return_value = mock_result
    mock_result.scalar.return_value = mock_order

    # Мокаем сессию и execute
    mock_session = MagicMock(spec=AsyncSession)
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Вызов функции
    result = await orm_get_order_details(mock_session, 1)

    # Проверки
    assert result is mock_order
    mock_session.execute.assert_awaited_once()

    # Проверка логов
    # Для проверки логов можно использовать pytest cap-log
    # (в этом примере проверки опущены для краткости)


@pytest.mark.asyncio
async def test_order_not_found():
    mock_result = MagicMock()
    mock_result.unique.return_value = mock_result
    mock_result.scalar.return_value = None

    mock_session = MagicMock(spec=AsyncSession)
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await orm_get_order_details(mock_session, 999)

    assert result is None


@pytest.mark.asyncio
async def test_database_error_handling():
    mock_session = MagicMock(spec=AsyncSession)
    mock_session.execute = AsyncMock(side_effect=SQLAlchemyError("DB Error"))

    with pytest.raises(SQLAlchemyError):
        await orm_get_order_details(mock_session, 1)


@pytest.mark.asyncio
async def test_data_structure():
    # Создаем тестовые данные
    test_product = Product(id=101, name="Test Product")
    test_item = OrderItem(id=10, product=test_product, quantity=2)
    test_order = Order(id=1, items=[test_item])

    # Мокаем результат
    mock_result = MagicMock()
    mock_result.unique.return_value = mock_result
    mock_result.scalar.return_value = test_order

    mock_session = MagicMock(spec=AsyncSession)
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Вызов и проверки
    order = await orm_get_order_details(mock_session, 1)

    assert order.id == 1
    assert len(order.items) == 1
    assert order.items[0].product.name == "Test Product"


@pytest.mark.asyncio
async def test_successful_status_update():
    # Мокаем сессию и результат execute
    mock_result = MagicMock()
    mock_result.rowcount = 1  # Симулируем успешное обновление

    mock_session = MagicMock(spec=AsyncSession)
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.commit = AsyncMock()

    # Вызываем функцию
    await orm_update_order_status(mock_session, 1, "completed")

    # Проверки
    mock_session.execute.assert_awaited_once()
    mock_session.commit.assert_awaited_once()

    # Проверка аргументов запроса
    args, _ = mock_session.execute.call_args
    generated_query = args[0]
    assert str(generated_query) == str(
        update(Order)
        .where(Order.id == 1)
        .values(status="completed")
    )


@pytest.mark.asyncio
async def test_order_not_found():
    mock_result = MagicMock()
    mock_result.rowcount = 0  # Заказ не найден

    mock_session = MagicMock(spec=AsyncSession)
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.commit = AsyncMock()

    await orm_update_order_status(mock_session, 999, "completed")

    mock_session.execute.assert_awaited_once()
    mock_session.commit.assert_not_awaited()  # commit не должен вызываться


@pytest.mark.asyncio
async def test_database_error_handling():
    mock_session = MagicMock(spec=AsyncSession)
    mock_session.execute = AsyncMock(side_effect=SQLAlchemyError("DB Error"))

    with pytest.raises(SQLAlchemyError):
        await orm_update_order_status(mock_session, 1, "completed")


@pytest.mark.asyncio
async def test_commit_error_handling():
    mock_result = MagicMock()
    mock_result.rowcount = 1

    mock_session = MagicMock(spec=AsyncSession)
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.commit = AsyncMock(side_effect=SQLAlchemyError("Commit Error"))

    with pytest.raises(SQLAlchemyError):
        await orm_update_order_status(mock_session, 1, "completed")


@pytest.mark.asyncio
async def test_logging(caplog):
    mock_result = MagicMock()
    mock_result.rowcount = 1
    mock_session = MagicMock(spec=AsyncSession)
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.commit = AsyncMock()

    with caplog.at_level(logging.INFO):
        await orm_update_order_status(mock_session, 1, "completed")

    # Проверка логов
    assert f"Обновление статуса заказа 1 на 'completed'" in caplog.text
    assert f"Статус заказа 1 успешно обновлен на 'completed'" in caplog.text


@pytest.mark.asyncio
async def test_successful_orders_retrieval():
    # Создаем тестовые данные
    mock_order1 = MagicMock(spec=Order, id=1, created="2023-10-01")
    mock_order2 = MagicMock(spec=Order, id=2, created="2023-10-02")
    mock_order1.items = [MagicMock(spec=OrderItem)]
    mock_order2.items = [MagicMock(spec=OrderItem)]

    # Мокаем результат запроса
    mock_result = MagicMock()
    mock_result.unique.return_value = mock_result
    mock_result.scalars.return_value = [mock_order2, mock_order1]  # Сортировка по убыванию

    mock_session = MagicMock(spec=AsyncSession)
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Вызов функции
    orders = await orm_get_user_orders(mock_session, 123)

    # Проверки
    assert len(orders) == 2
    assert orders[0].id == 2  # Проверка сортировки
    assert orders[1].id == 1
    assert len(orders[0].items) == 1  # Проверка загрузки items

    # Проверка структуры запроса
    args, _ = mock_session.execute.call_args
    generated_query = args[0]
    expected_query = (
        select(Order)
        .where(Order.user_id == 123)
        .options(joinedload(Order.items))
        .order_by(desc(Order.created))
    )
    assert str(generated_query) == str(expected_query)

@pytest.mark.asyncio
async def test_no_orders_found():
    mock_result = MagicMock()
    mock_result.unique.return_value = mock_result
    mock_result.scalars.return_value = []

    mock_session = MagicMock(spec=AsyncSession)
    mock_session.execute = AsyncMock(return_value=mock_result)

    orders = await orm_get_user_orders(mock_session, 999)
    assert len(orders) == 0

@pytest.mark.asyncio
async def test_database_error_handling():
    mock_session = MagicMock(spec=AsyncSession)
    mock_session.execute = AsyncMock(side_effect=SQLAlchemyError("DB Error"))

    with pytest.raises(SQLAlchemyError):
        await orm_get_user_orders(mock_session, 123)

@pytest.mark.asyncio
async def test_logging(caplog):
    mock_result = MagicMock()
    mock_result.unique.return_value = mock_result
    mock_result.scalars.return_value = [MagicMock(), MagicMock()]

    mock_session = MagicMock(spec=AsyncSession)
    mock_session.execute = AsyncMock(return_value=mock_result)

    with caplog.at_level(logging.INFO):
        await orm_get_user_orders(mock_session, 123)

    # Проверка логов
    assert "Получение списка заказов для пользователя 123" in caplog.text
    assert "Найдено 2 заказов для пользователя 123" in caplog.messages


# Тесты для orm_create_order
@pytest.mark.asyncio
async def test_orm_create_order_success():
    mock_session = MagicMock(spec=AsyncSession)
    mock_session.flush = AsyncMock()
    mock_order = MagicMock(spec=Order, id=1)

    with patch("your_module.Order", return_value=mock_order):
        order = await orm_create_order(
            session=mock_session,
            user_id=123,
            total_price=100.5,
            address="ул. Пушкина",
            phone="+79991234567",
            status="processing"
        )

    # Проверка создания Order
    assert order is mock_order
    mock_session.add.assert_called_once_with(mock_order)
    mock_session.flush.assert_awaited_once()

    # Проверка параметров
    assert order.user_id == 123
    assert order.total_price == 100.5
    assert order.address == "ул. Пушкина"

@pytest.mark.asyncio
async def test_orm_create_order_default_params():
    mock_session = MagicMock(spec=AsyncSession)
    mock_session.flush = AsyncMock()

    order = await orm_create_order(
        session=mock_session,
        user_id=123,
        total_price=100.5
    )

    # Проверка дефолтных значений
    assert order.status == "pending"
    assert order.address is None
    assert order.phone is None

# Тесты для orm_add_order
@pytest.mark.asyncio
async def test_orm_add_order_success():
    mock_session = MagicMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()
    mock_order = MagicMock(spec=Order, id=1)
    test_items = [{"product_id": 1, "quantity": 2}]

    with (
        patch("your_module.orm_create_order", AsyncMock(return_value=mock_order)),
        patch("your_module.orm_add_order_items", AsyncMock()) as mock_add_items
    ):
        result = await orm_add_order(
            session=mock_session,
            user_id=123,
            total_price=100.5,
            items=test_items
        )

    # Проверка вызовов
    your_module.orm_create_order.assert_awaited_with(
        mock_session, 123, 100.5, None, None, "pending"
    )
    mock_add_items.assert_awaited_with(mock_session, 1, test_items)
    mock_session.commit.assert_awaited_once()
    assert result is mock_order

@pytest.mark.asyncio
async def test_orm_add_order_rollback_on_error():
    mock_session = MagicMock(spec=AsyncSession)
    mock_session.rollback = AsyncMock()
    test_items = [{"product_id": 1, "quantity": 2}]

    with (
        patch("your_module.orm_create_order", AsyncMock()),
        patch(
            "your_module.orm_add_order_items",
            AsyncMock(side_effect=Exception("Ошибка"))
        )
    ):
        with pytest.raises(RuntimeError) as exc:
            await orm_add_order(
                session=mock_session,
                user_id=123,
                total_price=100.5,
                items=test_items
            )

    # Проверка отката
    mock_session.rollback.assert_awaited_once()
    assert "Ошибка при создании заказа" in str(exc.value)

@pytest.mark.asyncio
async def test_orm_add_order_logging(caplog):
    mock_session = MagicMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()

    with (
        patch("your_module.orm_create_order", AsyncMock()),
        patch("your_module.orm_add_order_items", AsyncMock()),
        caplog.at_level(logging.INFO)
    ):
        await orm_add_order(
            session=mock_session,
            user_id=123,
            total_price=100.5,
            items=[]
        )

    # Проверка логов
    assert "Начало оформления заказа для пользователя 123" in caplog.text
    assert "успешно оформлен" in caplog.text