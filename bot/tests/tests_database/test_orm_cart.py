import logging
from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy import delete

from database.models import Cart
from database.orm_querys.orm_query_cart import orm_add_to_cart, orm_get_user_carts, orm_delete_from_cart, \
    orm_reduce_product_in_cart

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Тесты для orm_add_to_cart
@pytest.mark.asyncio
async def test_add_to_cart_new_item():
    """Добавление нового товара в корзину"""
    mock_session = AsyncMock()
    mock_session.execute.return_value = AsyncMock(scalar=Mock(return_value=None))

    result = await orm_add_to_cart(mock_session, 1, 123)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited()
    logger.info.assert_any_call("Товар 123 добавлен в корзину пользователя 1")
    assert isinstance(result, Cart)


@pytest.mark.asyncio
async def test_add_to_cart_existing_item():
    """Увеличение количества существующего товара"""
    mock_cart = Mock(quantity=1)
    mock_session = AsyncMock()
    mock_session.execute.return_value = AsyncMock(scalar=Mock(return_value=mock_cart))

    await orm_add_to_cart(mock_session, 1, 123)

    assert mock_cart.quantity == 2
    logger.info.assert_any_call("Количество товара 123 в корзине пользователя 1 увеличено до 2")


# Тесты для orm_get_user_carts
@pytest.mark.asyncio
async def test_get_user_carts_empty():
    """Запрос пустой корзины"""
    mock_session = AsyncMock()
    mock_session.execute.return_value = AsyncMock(scalars=Mock(return_value=Mock(all=Mock(return_value=[]))))

    result = await orm_get_user_carts(mock_session, 1)

    assert len(result) == 0
    logger.info.assert_called_with("Найдено 0 товаров в корзине пользователя 1")


@pytest.mark.asyncio
async def test_get_user_carts_with_items():
    """Запрос корзины с товарами"""
    mock_items = [Mock(), Mock()]
    mock_session = AsyncMock()
    mock_session.execute.return_value = AsyncMock(scalars=Mock(return_value=Mock(all=Mock(return_value=mock_items))))

    result = await orm_get_user_carts(mock_session, 1)

    assert len(result) == 2
    logger.info.assert_called_with("Найдено 2 товаров в корзине пользователя 1")


# Тесты для orm_delete_from_cart
@pytest.mark.asyncio
async def test_delete_specific_item():
    """Удаление конкретного товара"""
    mock_session = AsyncMock()
    mock_session.execute.return_value = AsyncMock(scalars=Mock(return_value=Mock(all=Mock(return_value=[Mock()]))))

    await orm_delete_from_cart(mock_session, 1, 123)

    expected_query = delete(Cart).where(Cart.user_id == 1, Cart.product_id == 123)
    mock_session.execute.assert_any_call(expected_query)
    logger.info.assert_called_with("Товар 123 удален из корзины пользователя 1")


@pytest.mark.asyncio
async def test_delete_all_items():
    """Удаление всех товаров пользователя"""
    mock_session = AsyncMock()
    await orm_delete_from_cart(mock_session, 1)

    expected_query = delete(Cart).where(Cart.user_id == 1)
    mock_session.execute.assert_any_call(expected_query)
    logger.info.assert_called_with("Все товары удалены из корзины пользователя 1")


# Тесты для orm_reduce_product_in_cart
@pytest.mark.asyncio
async def test_reduce_quantity():
    """Уменьшение количества товара"""
    mock_cart = Mock(quantity=2)
    mock_session = AsyncMock()
    mock_session.execute.return_value = AsyncMock(scalar=Mock(return_value=mock_cart))

    result = await orm_reduce_product_in_cart(mock_session, 1, 123)

    assert mock_cart.quantity == 1
    assert result is True
    logger.info.assert_called_with("Количество товара 123 уменьшено до 1 в корзине пользователя 1")


@pytest.mark.asyncio
async def test_remove_item_when_quantity_one():
    """Удаление товара при количестве 1"""
    mock_cart = Mock(quantity=1)
    mock_session = AsyncMock()
    mock_session.execute.return_value = AsyncMock(scalar=Mock(return_value=mock_cart))

    result = await orm_reduce_product_in_cart(mock_session, 1, 123)

    mock_session.execute.assert_any_call(delete(Cart))
    assert result is False
    logger.info.assert_called_with("Товар 123 полностью удален из корзины пользователя 1")