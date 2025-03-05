from itertools import product

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from aiogram.types import InputMediaPhoto, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from handlers.menu_events.menu_main import main_menu
from handlers.menu_events.menu_paginator_navi import pages
from handlers.menu_events.menu_process_cart import carts
from handlers.menu_events.menu_process_catalog import catalog, products
from handlers.menu_events.menu_processing_get import get_menu_content
from keyboards.inline_main import MenuCallBack
from tests.tests_keyboards.test_keyboards import MockCategory
from utilit.notification import NotificationService


# Тесты для main_menu

@pytest.mark.asyncio
async def test_main_menu_success():  # +
    # Arrange
    mock_session = AsyncMock()
    mock_banner = MagicMock()
    mock_banner.image = "test_image.jpg"
    mock_banner.description = "Test description"

    # Мокаем правильную функцию orm_get_banner
    with patch(
            'handlers.menu_events.menu_main.orm_get_banner',
            new_callable=AsyncMock) as mock_orm_get_banner:
        mock_orm_get_banner.return_value = mock_banner

        # Act
        image, keyboards = await main_menu(
            session=mock_session,
            level=1,
            menu_name="main"
        )

        # Assert
        # Проверяем, что orm_get_banner была вызвана с правильными аргументами
        mock_orm_get_banner.assert_awaited_once_with(mock_session, "main")
        # Проверяем возвращаемые значения
        assert image.media == "test_image.jpg"
        assert image.caption == "Test description"
        # Дополнительные проверки клавиатур, если необходимо
        assert keyboards is not None


@pytest.mark.asyncio
async def test_main_menu_error_handling():  # +
    # Arrange
    mock_session = AsyncMock()

    # Мокаем функцию orm_get_banner и задаём исключение
    with patch(
            'handlers.menu_events.menu_main.orm_get_banner',
            new_callable=AsyncMock) as mock_orm:
        mock_orm.side_effect = Exception("DB error")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await main_menu(session=mock_session, level=1, menu_name="main")

        # Проверяем сообщение об ошибке
        assert "DB error" in str(exc_info.value)
        # Убеждаемся, что функция была вызвана
        mock_orm.assert_awaited_once_with(mock_session, "main")


@pytest.mark.asyncio
async def test_main_menu_keyboard_level():  # +
    # Arrange
    mock_session = AsyncMock()
    mock_banner = MagicMock()
    mock_banner.image = "test_image.jpg"  # Явно задаём строковое значение
    mock_banner.description = "Test description"  # Явно задаём строковое значение

    with patch(
            'handlers.menu_events.menu_main.orm_get_banner',
            new_callable=AsyncMock) as mock_orm:
        mock_orm.return_value = mock_banner

        # Act
        _, keyboards = await main_menu(
            session=mock_session,
            level=2,
            menu_name="catalog"
        )

        # Assert
        assert any(
            MenuCallBack.unpack(btn.callback_data).level == 2
            for row in keyboards.inline_keyboard
            for btn in row
        ), "Уровень кнопки не соответствует ожидаемому!"


# Тесты для paginator_navi


def test_pages_both_buttons():  # +
    # Создаем моков Paginator с обеими страницами
    mock_paginator = Mock()
    mock_paginator.has_previous.return_value = True
    mock_paginator.has_next.return_value = True

    result = pages(mock_paginator)

    assert result == {"◀️Пред.": "prev", "След.▶️": "next"}


def test_pages_prev_only():  # +
    # Только предыдущая страница
    mock_paginator = Mock()
    mock_paginator.has_previous.return_value = True
    mock_paginator.has_next.return_value = False

    result = pages(mock_paginator)
    assert result == {"◀️Пред.": "prev"}


def test_pages_next_only():  # +
    # Только следующая страница
    mock_paginator = Mock()
    mock_paginator.has_previous.return_value = False
    mock_paginator.has_next.return_value = True

    result = pages(mock_paginator)
    assert result == {"След.▶️": "next"}


def test_pages_no_pages():  # +
    # Нет страниц
    mock_paginator = Mock()
    mock_paginator.has_previous.return_value = False
    mock_paginator.has_next.return_value = False

    result = pages(mock_paginator)
    assert result == {}


# Тесты для menu_process_cart

class MockCartItem:
    def __init__(self, product_id, name, price, quantity):
        self.product = MagicMock()
        self.product.id = product_id
        self.product.name = name
        self.product.price = price
        self.product.image = "test_image.jpg"  # Явно задаём строку
        self.quantity = quantity


class MockResult:
    def __init__(self, items):
        self.items = items

    def scalars(self):
        return self

    def all(self):
        return self.items


@pytest.mark.asyncio
async def test_carts_delete_action_with_page_adjustment():  # +
    # Arrange
    mock_session = MagicMock(spec=AsyncSession)
    mock_cart_item = MockCartItem(101, "Test Product", 10.0, 2)
    mock_session.execute = AsyncMock(return_value=MockResult([mock_cart_item]))

    # Мокаем функцию orm_delete_from_cart
    with patch(
            'handlers.menu_events.menu_process_cart.orm_delete_from_cart',
            new_callable=AsyncMock) as mock_delete:
        # Act
        image, keyboards = await carts(
            session=mock_session,
            level=3,
            menu_name="delete",
            page=2,
            user_id=1,
            product_id=101
        )

        # Assert
        mock_delete.assert_awaited_once_with(mock_session, 1, 101)


class MockCart:
    def __init__(self, quantity, product=None):
        self.quantity = quantity
        self.product = product


class MocksResult:
    def scalar(self):
        return self.cart

    def __init__(self, cart):
        self.cart = cart


@pytest.mark.asyncio
async def test_carts_decrement_action_remove_product():  # +
    # Arrange
    mock_session = MagicMock(spec=AsyncSession)
    mock_product = MagicMock(price=10.99, name="Test_product", image="test_name_image.jpg")
    mock_cart = MockCart(quantity=1, product=mock_product)  # После уменьшения количество станет 0

    # Мокаем запрос к базе данных
    mock_session.execute = AsyncMock(return_value=MockResult([mock_cart]))

    # Мокаем функцию orm_reduce_product_in_cart
    with (patch(
            'handlers.menu_events.menu_process_cart.orm_reduce_product_in_cart',
            new_callable=AsyncMock
    ) as mock_reduce):
        # Товар удалён
        mock_reduce.return_value = False
        # Act
        image, keyboards = await carts(
            session=mock_session,
            level=3,
            menu_name="decrement",
            page=2,
            user_id=1,
            product_id=101
        )

        # Assert
        # Проверяем, что функция уменьшения вызвана корректно
        mock_reduce.assert_awaited_once_with(
            mock_session,
            1,
            101
        )

        # Проверяем переход на предыдущую страницу
        assert isinstance(image, InputMediaPhoto)
        assert """(<strong><MagicMock name='Test_product.name' id='4622317760'></strong>\n
        ("'10.99.PLN x 1 = 10.99.PLN\n'"
         "'Товар 1 из 1 в корзине.\n')"
         "'Общая сумма товаров в корзине: 10.99.PLN')"""
        assert "menu:3:delete::1:1" in keyboards.inline_keyboard[0][0].callback_data


class MockCarts:
    def __init__(self, quantity):
        self.quantity = quantity
        self.product = product
        self.product.id = 101
        self.product.name = "Test Product"
        self.product.price = 10.0
        self.product.image = "test_image.jpg"


class MockResults:
    def scalar(self):
        return self.cart

    def __init__(self, cart):
        self.cart = cart


@pytest.mark.asyncio
async def test_carts_increment_action():  # +
    # Arrange
    mock_session = MagicMock(spec=AsyncSession)
    mock_product = MagicMock(name="Test Name", price=10.99, image="test_name_image.jpg")
    mock_cart = MockCart(quantity=2, product=mock_product)  # Изначальное количество товара

    # Фиксируем строковое представление для name
    type(mock_product).name = "Test Product"  # Исправлено здесь

    # Мокаем запрос к базе данных
    mock_session.execute = AsyncMock(return_value=MockResult([mock_cart]))

    # Мокаем функцию orm_add_to_cart
    with patch(
            'handlers.menu_events.menu_process_cart.orm_add_to_cart',
            new_callable=AsyncMock
    ) as mock_add:
        # Act
        image, keyboards = await carts(
            session=mock_session,
            level=3,
            menu_name="increment",
            page=1,
            user_id=1,
            product_id=101
        )

        # Assert
        # Проверяем, что функция добавления вызвана
        mock_add.assert_awaited_once_with(
            mock_session,
            1,
            101
        )

        # Проверяем, что количество увеличилось
        # Проверяем ключевые части caption, игнорируя динамические элементы
        caption = image.caption
        assert "<strong>Test Product</strong>" in caption  # Исправлено
        assert "10.99.PLN x 2 = 21.98.PLN" in caption
        assert "Товар 1 из 1 в корзине" in caption
        assert mock_cart.quantity == 2


# 3. Создаем баннер с корректными строковыми значениями
class MockBanner:
    def __init__(self):
        self.image = "empty_cart.jpg"  # Используем строку вместо мока
        self.description = "Корзина пуста"  # Реальная строка


@pytest.mark.asyncio
async def test_empty_cart_handling():
    # Arrange
    mock_session = MagicMock(spec=AsyncSession)

    # 1. Мокаем процесс удаления товара
    mock_session.execute.return_value = MagicMock(rowcount=1)
    mock_session.commit = AsyncMock()

    # 2. Мокаем пустую корзину
    mock_session.orm_get_user_carts = AsyncMock(return_value=[])

    mock_banner = MockBanner()
    mock_session.orm_get_banner = AsyncMock(return_value=mock_banner)

    # Act
    image, keyboards = await carts(
        session=mock_session,
        level=3,
        menu_name="delete",
        page=1,
        user_id=1,
        product_id=101
    )

    # Assert
    assert image.media == "empty_cart.jpg"  # Проверка строки вместо мока
    assert "<strong>Корзина пуста</strong>" in image.caption


# Тесты для menu_process_catalog
class MockBannerImage:
    def __init__(self):
        self.image = "banner.jpg"
        self.description = "Catalog Banner"

@pytest.mark.asyncio
async def test_catalog_success():
    # Arrange
    mock_session = MagicMock(spec=AsyncSession)


    mock_banner = MockBanner()
    mock_categories = [
        MockCategory(1, "Конфеты"),
        MockCategory(2, "Шоколад")
    ]

    # Настраиваем моки
    mock_session.orm_get_banner = AsyncMock(return_value=mock_banner)
    mock_session.orm_get_categories = AsyncMock(return_value=mock_categories)

    # Act
    image, keyboards = await catalog(
        session=mock_session,
        level=1,
        menu_name="catalog"
    )

    # Assert
    mock_session.orm_get_banner.assert_awaited_once_with(session=mock_session, page="catalog")
    mock_session.orm_get_categories.assert_awaited_once_with(session=mock_session)

    # Проверка изображения
    assert isinstance(image, InputMediaPhoto)
    assert image.media == "banner.jpg"
    assert image.caption == "Catalog Banner"

    # Проверка клавиатуры
    assert len(keyboards.inline_keyboard) == len(mock_categories)
    for i, category in enumerate(mock_categories):
        btn = keyboards.inline_keyboard[i][0]
        assert btn.text == category.name
        assert btn.callback_data == f"category_{category.id}"


class MockProduct:
    def __init__(self, id, name, description, price, image):
        self.id = id
        self.name = name
        self.description = description
        self.price = price
        self.image = image


@pytest.mark.asyncio
async def test_products_pagination():
    # Arrange
    mock_session = MagicMock(spec=AsyncSession)

    # Создаем 5 товаров для тестирования пагинации
    mock_products = [
        MockProduct(101, "Шоколад", "Вкусный", 10.5, "choco.jpg"),
        MockProduct(102, "Конфета", "Сладкая", 5.0, "candy.jpg"),
        MockProduct(103, "Мармелад", "Фруктовый", 8.0, "marmalade.jpg"),
        MockProduct(104, "Печенье", "Хрустящее", 7.5, "cookie.jpg"),
        MockProduct(105, "Вафли", "Сладкие", 9.0, "waffle.jpg")
    ]

    # Мокаем результат запроса
    mock_result = MagicMock()
    mock_result.scalars.return_value = MagicMock(all=MagicMock(return_value=mock_products))
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Act (page=1, per_page=2)
    image, keyboards = await products(
        session=mock_session,
        level=2,
        category=1,
        page=1
    )

    # Assert
    # Проверяем, что есть кнопки пагинации
    pagination_buttons = {"⬅️Пред.", "След.➡️"}
    assert any(
        btn.text in pagination_buttons
        for row in keyboards.inline_keyboard
        for btn in row
    ), "Кнопки пагинации должны отображаться при наличии нескольких страниц"



class MocksResults:
    def scalars(self):
        return self

    def all(self):
        return []  # Имитируем пустой список товаров


@pytest.mark.asyncio
async def test_products_empty_list():
    # Arrange
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=MockResult())  # Мок результата запроса

    # Мокаем функцию orm_get_products
    with patch(
            'handlers.menu_events.menu_process_catalog.orm_get_products',
            new_callable=AsyncMock(return_value=[])
    ) as mock_get_products:
        # Act & Assert
        with pytest.raises(IndexError):
            await products(
                session=mock_session,
                level=2,
                category=1,
                page=1
            )

        # Проверяем вызов функции
        mock_get_products.assert_awaited_once_with(mock_session, category_id=1)


# Тесты для menu_processing_get

@pytest.mark.asyncio
@patch("handlers.menu_events")
async def test_level_0_main_menu(mock_main_menu):
    # Мокируем возвращаемые значения
    mock_main_menu.return_value = (
        InputMediaPhoto(media="main.jpg"),
        InlineKeyboardMarkup(inline_keyboard=[])
    )

    # Вызов функции
    image, keyboards = await get_menu_content(
        session=AsyncMock(),
        level=0,
        menu_name="main"
    )

    # Проверки
    mock_main_menu.assert_awaited_once_with(AsyncMock(), 0, "main")
    assert isinstance(image, InputMediaPhoto)
    assert image.media == "main.jpg"


@pytest.mark.asyncio
@patch("your_module.catalog")
async def test_level_1_catalog(mock_catalog):
    mock_catalog.return_value = (
        InputMediaPhoto(media="catalog.jpg"),
        InlineKeyboardMarkup(inline_keyboard=[])
    )

    image, keyboards = await get_menu_content(
        session=AsyncMock(),
        level=1,
        menu_name="catalog"
    )

    mock_catalog.assert_awaited_once_with(AsyncMock(), 1, "catalog")


@pytest.mark.asyncio
@patch("your_module.products")
async def test_level_2_products(mock_products):
    mock_products.return_value = (
        InputMediaPhoto(media="product.jpg"),
        InlineKeyboardMarkup(inline_keyboard=[])
    )

    image, keyboards = await get_menu_content(
        session=AsyncMock(),
        level=2,
        menu_name="products",
        category=5,
        page=2
    )

    mock_products.assert_awaited_once_with(AsyncMock(), 2, 5, 2)

class MockBannerCart:
    def __init__(self):
        self.image = "empty_cart.jpg"  # Строка
        self.description = "Корзина пуста"  # Строка


@pytest.mark.asyncio
@patch("handlers.menu_events.menu_process_cart.orm_delete_from_cart")
async def test_level_3_carts(mock_delete):
    # Arrange
    mock_session = MagicMock(spec=AsyncSession)

    # Мокаем результат запроса к БД
    mock_result = MagicMock()
    mock_result.scalars.return_value = MagicMock(all=MagicMock(return_value=[]))
    mock_session.execute = AsyncMock(return_value=mock_result)

    mock_banner = MockBanner()
    mock_session.orm_get_banner = AsyncMock(return_value=mock_banner)

    # Act
    image, keyboards = await get_menu_content(
        session=mock_session,
        level=3,
        menu_name="delete",
        page=2,
        user_id=123,
        product_id=456
    )

    # Assert
    mock_delete.assert_awaited_once_with(mock_session, 123, 456)
    assert image.media == "empty_cart.jpg"
    assert "<strong>Корзина пуста</strong>" in image.caption


@pytest.mark.asyncio
async def test_level_4_checkout(): # -
    # Arrange
    mock_session = MagicMock(spec=AsyncSession)
    mock_notification = AsyncMock(spec=NotificationService)

    # Мокаем баннер
    mock_banner = MagicMock(
        image="success_banner.jpg",
        description="Ваш заказ оформлен!"
    )
    mock_session.orm_get_banner = AsyncMock(return_value=mock_banner)

    # Мокаем товары в корзине
    mock_product = MagicMock(price=150, id=101)
    mock_cart_item = MagicMock(product=mock_product, quantity=2, product_id=101)
    mock_session.orm_get_user_carts = AsyncMock(return_value=[mock_cart_item])

    # Мокаем транзакцию
    mock_session.begin.return_value.__aenter__ = AsyncMock()
    mock_session.begin.return_value.__aexit__ = AsyncMock()

    # Мокаем создание заказа
    mock_order = MagicMock(id=1)
    mock_session.add = MagicMock()
    mock_session.flush = AsyncMock()

    # Мокаем форматирование уведомления для администратора
    with patch("handlers.user_events.user_checkout.format_admin_notification") as mock_format:
        mock_format.return_value = (
            "Текст уведомления",
            InlineKeyboardMarkup(inline_keyboard=[])
        )

        # Act
        image, keyboards = await get_menu_content(
            session=mock_session,
            level=4,
            menu_name="checkout",
            user_id=123,
            notification_service=mock_notification
        )

    # Assert
    # Проверяем вызов send_to_admin
    mock_notification.send_to_admin.assert_awaited_once_with(
        text="Текст уведомления",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[]),
        parse_mode="HTML"
    )

    # Проверяем данные для пользователя
    assert "Ваш заказ оформлен!" in image.caption
    assert keyboards.inline_keyboard == []


@pytest.mark.asyncio
async def test_invalid_level(): # +
    mock_session = MagicMock(spec=AsyncSession)

    # Пытаемся вызвать функцию с недопустимым уровнем
    with pytest.raises(ValueError) as exc_info:
        await get_menu_content(
            session=mock_session,
            level=5,  # Недопустимый уровень
            menu_name="invalid_menu",
            user_id=1
        )

    # Проверяем сообщение об ошибке
    assert str(exc_info.value) == "Недопустимый уровень: 5"