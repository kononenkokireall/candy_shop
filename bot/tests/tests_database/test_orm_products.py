from unittest.mock import AsyncMock, Mock
import logging
import pytest
from sqlalchemy import update, delete

from database.models import Product
from database.orm_querys.orm_query_product import orm_add_product, orm_get_products, orm_get_product, \
    orm_update_product, orm_delete_product

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Тесты для orm_add_product
@pytest.mark.asyncio
async def test_orm_add_product_success():
    """Успешное добавление товара"""
    mock_session = AsyncMock()
    test_data = {
        "name": "Телефон",
        "description": "Смартфон",
        "price": "299.99",
        "image": "phone.jpg",
        "category": "1"
    }

    await orm_add_product(mock_session, test_data)

    # Проверка создания объекта
    mock_session.add.assert_called_once()
    added_product = mock_session.add.call_args[0][0]
    assert isinstance(added_product, Product)
    assert added_product.name == "Телефон"

    # Проверка commit и логов
    mock_session.commit.assert_awaited_once()
    logger.info.assert_any_call("Товар 'Телефон' успешно добавлен в категорию 1")


@pytest.mark.asyncio
async def test_orm_add_product_invalid_data():
    """Попытка добавления с неверными данными"""
    mock_session = AsyncMock()
    invalid_data = {"name": "Ноутбук"}  # Неполные данные

    with pytest.raises(Exception):
        await orm_add_product(mock_session, invalid_data)

    mock_session.rollback.assert_awaited()
    logger.exception.assert_called()


# Тесты для orm_get_products
@pytest.mark.asyncio
async def test_orm_get_products_success():
    """Успешное получение товаров категории"""
    mock_products = [Mock(), Mock()]
    mock_session = AsyncMock()
    mock_session.execute.return_value = AsyncMock(
        scalars=Mock(return_value=Mock(all=Mock(return_value=mock_products)))
    )

    result = await orm_get_products(mock_session, 1)

    assert len(result) == 2
    logger.info.assert_any_call("Найдено 2 товаров в категории 1")


@pytest.mark.asyncio
async def test_orm_get_products_empty():
    """Получение товаров несуществующей категории"""
    mock_session = AsyncMock()
    mock_session.execute.return_value = AsyncMock(
        scalars=Mock(return_value=Mock(all=Mock(return_value=[])))
    )

    result = await orm_get_products(mock_session, 999)

    assert len(result) == 0
    logger.info.assert_any_call("Найдено 0 товаров в категории 999")


# Тесты для orm_get_product
@pytest.mark.asyncio
async def test_orm_get_product_found():
    """Успешное получение товара по ID"""
    mock_product = Mock(id=1, name="Планшет")
    mock_session = AsyncMock()
    mock_session.execute.return_value = AsyncMock(scalar=Mock(return_value=mock_product))

    result = await orm_get_product(mock_session, 1)

    assert result == mock_product
    logger.info.assert_any_call("Товар 1 найден: Планшет")


@pytest.mark.asyncio
async def test_orm_get_product_not_found():
    """Поиск несуществующего товара"""
    mock_session = AsyncMock()
    mock_session.execute.return_value = AsyncMock(scalar=Mock(return_value=None))

    result = await orm_get_product(mock_session, 999)

    assert result is None
    logger.warning.assert_called_with("Товар 999 не найден")


# Тесты для orm_update_product
@pytest.mark.asyncio
async def test_orm_update_product_success():
    """Успешное обновление товара"""
    mock_session = AsyncMock()
    test_data = {
        "name": "Новое название",
        "description": "Новое описание",
        "price": "399.99",
        "image": "new.jpg",
        "category": "2"
    }

    await orm_update_product(mock_session, 1, test_data)

    # Проверка формирования запроса
    expected_query = update(Product).where(Product.id == 1).values(
        name="Новое название",
        description="Новое описание",
        price=399.99,
        image="new.jpg",
        category_id=2
    )
    mock_session.execute.assert_awaited_once_with(expected_query)
    logger.info.assert_any_call("Товар 1 обновлен: Новое название")


# Тесты для orm_delete_product
@pytest.mark.asyncio
async def test_orm_delete_product_success():
    """Успешное удаление товара"""
    mock_session = AsyncMock()

    await orm_delete_product(mock_session, 1)

    expected_query = delete(Product).where(Product.id == 1)
    mock_session.execute.assert_awaited_once_with(expected_query)
    logger.info.assert_any_call("Товар 1 успешно удален")


@pytest.mark.asyncio
async def test_orm_delete_product_not_found():
    """Попытка удаления несуществующего товара"""
    mock_session = AsyncMock()
    mock_session.execute.side_effect = Exception("Товар не найден")

    with pytest.raises(Exception):
        await orm_delete_product(mock_session, 999)

    logger.exception.assert_called_with("Ошибка при удалении товара 999: Товар не найден")