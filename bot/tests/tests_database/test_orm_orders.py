from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy import update, delete

from database.models import Order
from database.orm_querys.orm_query_order import (
    orm_add_order,
    orm_create_order,
    orm_add_order_items,
    orm_get_user_orders,
    orm_get_order_details,
    orm_update_order_status,
    get_order_by_id,
    orm_delete_order
)


# Тесты для orm_add_order
@pytest.mark.asyncio
async def test_orm_add_order_success():
    """Успешное создание заказа с валидными данными"""
    mock_session = AsyncMock()
    mock_session.execute.return_value = AsyncMock(all=Mock(return_value=[(1,), (2,)]))

    items = [
        {"product_id": 1, "quantity": 2, "price": 100.0},
        {"product_id": 2, "quantity": 1, "price": 200.0}
    ]

    await orm_add_order(
        session=mock_session,
        user_id=123,
        total_price=400.0,
        items=items
    )

    mock_session.add.assert_any_call(Mock(spec=Order))
    mock_session.flush.assert_awaited_once()
    assert mock_session.add.call_count == 3


@pytest.mark.asyncio
async def test_orm_add_order_invalid_items():
    """Попытка создания заказа с невалидными items"""
    mock_session = AsyncMock()

    with pytest.raises(ValueError):
        await orm_add_order(
            session=mock_session,
            user_id=123,
            total_price=100.0,
            items={"product_id": 1, "quantity": 1, "price": 100.0}
        )


# Тесты для orm_create_order
@pytest.mark.asyncio
async def test_orm_create_order_success():
    """Успешное создание заказа"""
    mock_session = AsyncMock()
    mock_order = Mock(id=1, user_id=123, total_price=500.0)
    mock_session.add.return_value = mock_order

    result = await orm_create_order(
        session=mock_session,
        data={"user_id": 123, "total_price": 500.0}
    )

    assert isinstance(result, Order)


# Тесты для orm_add_order_items
@pytest.mark.asyncio
async def test_orm_add_order_items_success():
    """Успешное добавление элементов заказа"""
    mock_session = AsyncMock()
    items = [
        {"product_id": 1, "quantity": 3, "price": 150.0},
        {"product_id": 2, "quantity": 2, "price": 300.0}
    ]

    await orm_add_order_items(mock_session, 1, items)
    assert mock_session.add.call_count == 2


# Тесты для orm_get_user_orders
@pytest.mark.asyncio
async def test_orm_get_user_orders_success():
    """Получение заказов пользователя"""
    mock_session = AsyncMock()
    mock_orders = [Mock(), Mock()]
    mock_session.execute.return_value = AsyncMock(
        unique=Mock(
            return_value=Mock(
                scalars=Mock(
                    return_value=Mock(
                        all=Mock(return_value=mock_orders)
                    )
                )
            )
        )
    )

    result = await orm_get_user_orders(mock_session, 123)
    assert len(result) == 2


# Тесты для orm_get_order_details
@pytest.mark.asyncio
async def test_orm_get_order_details_found():
    """Получение деталей существующего заказа"""
    mock_session = AsyncMock()
    mock_order = Mock(id=1, items=[Mock(), Mock()])
    mock_session.execute.return_value = AsyncMock(
        unique=Mock(
            return_value=Mock(
                scalar=Mock(return_value=mock_order)
            )
        )
    )

    result = await orm_get_order_details(mock_session, 1)
    assert result == mock_order


# Тесты для orm_update_order_status
@pytest.mark.asyncio
async def test_orm_update_order_status_success():
    """Обновление статуса заказа"""
    mock_session = AsyncMock()
    await orm_update_order_status(mock_session, 1, "completed")

    expected_query = update(Order).where(Order.id == 1).values(status="completed")
    mock_session.execute.assert_awaited_once_with(expected_query)


# Тесты для get_order_by_id
@pytest.mark.asyncio
async def test_get_order_by_id_found():
    """Поиск существующего заказа"""
    mock_session = AsyncMock()
    mock_order = Mock(id=1)
    mock_session.execute.return_value = AsyncMock(
        scalar_one_or_none=Mock(return_value=mock_order)
    )

    result = await get_order_by_id(mock_session, 1)
    assert result == mock_order


# Тесты для orm_delete_order
@pytest.mark.asyncio
async def test_orm_delete_order_success():
    """Удаление заказа"""
    mock_session = AsyncMock()
    await orm_delete_order(mock_session, 1)

    expected_query = delete(Order).where(Order.id == 1)
    mock_session.execute.assert_awaited_once_with(expected_query)