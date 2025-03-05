from unittest.mock import patch

import pytest
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup

from keyboards.inline_cart import get_user_cart_btn
from keyboards.inline_catalog import get_user_catalog_btn
from keyboards.inline_main import MenuCallBack, OrderCallbackData, get_user_main_btn, get_callback_btn
from keyboards.inline_product import get_user_product_btn
from keyboards.linline_admin import OrderAction, build_admin_keyboard, build_user_keyboard
from keyboards.reply import get_keyboard


# Тесты для def get_keyboard
def test_basic_keyboard_creation():
    keyboard = get_keyboard(
        "Кнопка 1", "Кнопка 2", "Кнопка 3",
        sizes=(2, 1))

    assert isinstance(keyboard, ReplyKeyboardMarkup)
    assert len(keyboard.keyboard) == 2  # 2 ряда
    assert len(keyboard.keyboard[0]) == 2  # Первый ряд: 2 кнопки
    assert len(keyboard.keyboard[1]) == 1  # Второй ряд: 1 кнопка


def test_special_buttons():
    keyboard = get_keyboard(
        "Обычная", "Телефон", "Локация",
        request_contact=1,
        request_location=2,
        sizes=(3,))

    # Проверка request_contact
    contact_btn = keyboard.keyboard[0][1]
    assert contact_btn.request_contact is True

    # Проверка request_location
    location_btn = keyboard.keyboard[0][2]
    assert location_btn.request_location is True


def test_placeholder():
    placeholder_text = "Выберите вариант"
    keyboard = get_keyboard(
        "Да", "Нет",
        placeholder=placeholder_text
    )

    assert keyboard.input_field_placeholder == placeholder_text


def test_keyboard_sizes():
    keyboard = get_keyboard(
        "A", "B", "C", "D", "E",
        sizes=tuple[int](2, ))

    assert len(keyboard.keyboard) == 3
    assert len(keyboard.keyboard[0]) == 2  # Первые 2 кнопки
    assert len(keyboard.keyboard[1]) == 2  # Следующие 2
    assert len(keyboard.keyboard[2]) == 1  # Последняя


# Тесты для def build_admin_keyboard/build_user_keyboard/class OrderAction


def test_placeholders():
    # Проверка плейсхолдера
    markup = get_keyboard("Да", "Нет", placeholder="Выберите вариант")
    assert markup.input_field_placeholder == "Выберите вариант"


def test_empty_buttons():
    # Крайний случай: пустая клавиатура
    markup = get_keyboard(sizes=tuple[int]())
    assert len(markup.keyboard) == 0


# Тесты для build_admin_keyboard/build_user_keyboard


# Тесты для OrderAction
def test_order_action_callback():
    # Проверка сериализации
    callback = OrderAction(action="confirm", order_id=123)
    packed = callback.pack()
    assert packed.startswith("order:confirm:123")

    # Проверка десериализации
    unpacked = OrderAction.unpack(packed)
    assert unpacked.action == "confirm"
    assert unpacked.order_id == 123


# Тесты для build_admin_keyboard
def test_admin_keyboard_structure():
    order_id = 456
    keyboard = build_admin_keyboard(order_id)

    assert isinstance(keyboard, InlineKeyboardMarkup)
    assert len(keyboard.inline_keyboard) == 1  # Один ряд
    assert len(keyboard.inline_keyboard[0]) == 2  # Две кнопки

    # Проверка кнопки "Подтвердить"
    confirm_btn = keyboard.inline_keyboard[0][0]
    assert confirm_btn.text == "✅ Подтвердить"
    confirm_data = OrderAction.unpack(confirm_btn.callback_data)
    assert confirm_data.action == "confirm"
    assert confirm_data.order_id == order_id

    # Проверка кнопки "Отменить"
    cancel_btn = keyboard.inline_keyboard[0][1]
    assert cancel_btn.text == "❌ Отменить"
    cancel_data = OrderAction.unpack(cancel_btn.callback_data)
    assert cancel_data.action == "cancel"
    assert cancel_data.order_id == order_id


# Тесты для build_user_keyboard
@patch("utilit.config", "12345")  # TODO
def test_user_keyboard_structure():
    keyboard = build_user_keyboard()

    assert isinstance(keyboard, InlineKeyboardMarkup)
    assert len(keyboard.inline_keyboard) == 2  # Два ряда

    # Проверка кнопки чата
    chat_btn = keyboard.inline_keyboard[0][0]
    assert chat_btn.text == "Чат с админом 💬"
    assert chat_btn.url == "tg://user?id=7552593310"

    # Проверка кнопки возврата
    back_btn = keyboard.inline_keyboard[1][0]
    assert back_btn.text == "🏠Обратно в меню"
    back_data = MenuCallBack.unpack(back_btn.callback_data)
    assert back_data.level == 0
    assert back_data.menu_name == "main"


def test_edge_cases():
    # Проверка нулевого order_id
    keyboard = build_admin_keyboard(0)
    confirm_data = OrderAction.unpack(keyboard.inline_keyboard[0][0].callback_data)
    assert confirm_data.order_id == 0


# Тесты для get_user_product_btn


def test_basic_keyboard_structure():
    keyboard = get_user_product_btn(
        level=2,
        category=5,
        page=1,
        product_id=10,
        sizes=tuple[int](2, ))

    assert isinstance(keyboard, InlineKeyboardMarkup)

    # Проверка основных кнопок
    assert len(keyboard.inline_keyboard) == 2  # 2 ряда из-за sizes=(2,1)

    # Кнопка "◀️Вернутся"
    back_btn = keyboard.inline_keyboard[0][0]
    back_data = MenuCallBack.unpack(back_btn.callback_data)
    assert back_data.level == 1  # level-1
    assert back_data.menu_name == "catalog"

    # Кнопка "Корзина 🛒"
    cart_btn = keyboard.inline_keyboard[0][1]
    cart_data = MenuCallBack.unpack(cart_btn.callback_data)
    assert cart_data.level == 3

    # Кнопка "Купить 💵"
    buy_btn = keyboard.inline_keyboard[1][0]
    buy_data = MenuCallBack.unpack(buy_btn.callback_data)
    assert buy_data.menu_name == "add_to_cart"
    assert buy_data.product_id == 10


def test_pagination():
    keyboard = get_user_product_btn(
        level=2,
        category=5,
        page=2,
        pagination_btn={"➡️": "next", "⬅️": "prev"},
        product_id=10
    )

    # Проверка пагинации
    assert len(keyboard.inline_keyboard) == 3  # 2 ряда основных + 1 ряд пагинации

    # Кнопка "next"
    next_btn = keyboard.inline_keyboard[2][0]
    next_data = MenuCallBack.unpack(next_btn.callback_data)
    assert next_data.page == 3
    assert next_data.menu_name == "next"

    # Кнопка "prev"
    prev_btn = keyboard.inline_keyboard[2][1]
    prev_data = MenuCallBack.unpack(prev_btn.callback_data)
    assert prev_data.page == 1


def test_sizes_adjustment():
    keyboard = get_user_product_btn(
        level=2,
        category=5,
        page=1,
        product_id=10,
        sizes=(3,)
    )

    # Все основные кнопки в одном ряду
    assert len(keyboard.inline_keyboard[0]) == 3


def test_edge_case():
    # Пустая пагинация
    keyboard = get_user_product_btn(
        level=2,
        category=5,
        page=0,
        pagination_btn={"Wrong": "invalid"},
        product_id=10
    )
    assert len(keyboard.inline_keyboard) == 2  # Только основные кнопки

    # Отрицательная страница
    keyboard = get_user_product_btn(
        level=1,
        category=5,
        page=-1,
        pagination_btn={"⬅️": "prev"},
        product_id=10
    )
    prev_data = MenuCallBack.unpack(keyboard.inline_keyboard[2][0].callback_data)
    assert prev_data.page == -2


# Тест для get_user_main_btn/get_callback_btn


# Тесты для MenuCallBack
def test_menu_callback_data():
    callback = MenuCallBack(
        level=2,
        menu_name="catalog",
        category=5,
        product_id=10
    )
    packed = callback.pack()
    unpacked = MenuCallBack.unpack(packed)

    assert unpacked.level == 2
    assert unpacked.menu_name == "catalog"
    assert unpacked.category == 5
    assert unpacked.product_id == 10
    assert packed.startswith("menu:")


# Тесты для OrderCallbackData
def test_order_callback_data():
    callback = OrderCallbackData(action="confirm", user_id=123)
    packed = callback.pack()

    assert "order:confirm" in packed
    assert OrderCallbackData.unpack(packed).user_id == 123


# Тесты для get_user_main_btn
def test_get_user_main_btn():
    keyboard = get_user_main_btn(level=1, sizes=(2, 2, 1))

    assert isinstance(keyboard, InlineKeyboardMarkup)
    assert len(keyboard.inline_keyboard) == 3  # 2+2+1 кнопок

    # Проверка кнопки каталога
    catalog_btn = next(
        btn for row in keyboard.inline_keyboard
        for btn in row if btn.text == "Товары 🍭 💨"
    )
    data = MenuCallBack.unpack(catalog_btn.callback_data)
    assert data.level == 2  # 1+1


# Тесты для get_callback_btn
def test_get_callback_btn():
    test_buttons = {
        "Да": "yes",
        "Нет": "no",
        "Отмена": "cancel"
    }

    keyboard = get_callback_btn(btn=test_buttons, sizes=(2, 1))

    assert len(keyboard.inline_keyboard) == 2
    assert len(keyboard.inline_keyboard[0]) == 2
    assert keyboard.inline_keyboard[1][0].callback_data == "cancel"


@pytest.mark.parametrize("level,sizes,expected", [
    (0, (3,), 2),  # 3 кнопки в первом ряду + 2 во втором
    (2, (1,), 5),  # 5 рядов по 1 кнопке
    (1, (5,), 1),  # все кнопки в одном ряду
])
def test_keyboard_sizes(level, sizes, expected):
    keyboard = get_user_main_btn(level=level, sizes=sizes)
    assert len(keyboard.inline_keyboard) == expected


def test_edge_btn_cases():
    # Пустая клавиатура
    empty_kb = get_callback_btn(btn={}, sizes=(2,))
    assert len(empty_kb.inline_keyboard) == 0

    # Некорректный уровень
    with pytest.raises(ValueError):
        MenuCallBack(level=-1, menu_name="invalid")


# Тесты для get_user_catalog_btn


class MockCategory:
    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name


def test_catalog_keyboard_basic_structure():
    # Создаем моковые категории
    categories = [
        MockCategory(1, "Конфеты"),
        MockCategory(2, "Шоколад")
    ]

    keyboard = get_user_catalog_btn(
        level=2,
        categories=categories,
        sizes=(2,)
    )

    assert isinstance(keyboard, InlineKeyboardMarkup)

    # Проверяем обязательные кнопки
    assert any(
        btn.text == "◀️Вернутся"
        and MenuCallBack.unpack(btn.callback_data).level == 1
        for row in keyboard.inline_keyboard
        for btn in row
    )

    assert any(
        btn.text == "Корзина 🛒"
        and MenuCallBack.unpack(btn.callback_data).level == 3
        for row in keyboard.inline_keyboard
        for btn in row
    )

    # Проверяем кнопки категорий
    category_buttons = [
        btn for row in keyboard.inline_keyboard
        for btn in row
        if btn.text in {"Конфеты", "Шоколад"}
    ]
    assert len(category_buttons) == 2


def test_category_buttons_data():
    categories = [MockCategory(5, "Мармелад")]
    keyboard = get_user_catalog_btn(
        level=1,
        categories=categories,
        sizes=(1,)
    )

    category_btn = next(
        btn for row in keyboard.inline_keyboard
        for btn in row
        if btn.text == "Мармелад"
    )
    data = MenuCallBack.unpack(category_btn.callback_data)

    assert data.level == 2
    assert data.menu_name == "Мармелад"
    assert data.category == 5


@pytest.mark.parametrize("sizes,expected_total_rows", [
    ((2,), 3),  # 1 ряд основных + 2 ряда категорий
    ((1, 1), 6),  # 2 ряда основных + 4 ряда категорий
    ((3,), 2),  # 1 ряд (основные + категория) + 1 ряд категорий
])
def test_keyboard_sizes(sizes, expected_total_rows):
    categories = [MockCategory(i, f"Cat{i}") for i in range(4)]
    keyboard = get_user_catalog_btn(
        level=2,
        categories=categories,
        sizes=sizes
    )
    assert len(keyboard.inline_keyboard) == expected_total_rows


def test_empty_categories():
    keyboard = get_user_catalog_btn(
        level=2,
        categories=[],
        sizes=(2,)
    )

    # Только кнопки Назад и Корзина
    assert sum(len(row) for row in keyboard.inline_keyboard) == 2
    assert all(btn.text in {"◀️Вернутся", "Корзина 🛒"}
               for row in keyboard.inline_keyboard
               for btn in row)


def test_pagination_with_different_levels():
    categories = [MockCategory(1, "Test")]

    for level in [1, 3, 5]:
        keyboard = get_user_catalog_btn(
            level=level,
            categories=categories,
            sizes=(1,)
        )
        category_btn = next(
            btn for row in keyboard.inline_keyboard
            for btn in row
            if btn.text == "Test"
        )
        data = MenuCallBack.unpack(category_btn.callback_data)
        assert data.level == level + 1


# Тесты для get_user_cart_btn

def test_cart_with_page():
    keyboard = get_user_cart_btn(
        level=2,
        page=3,
        pagination_btn={"➡️": "next", "⬅️": "prev"},
        product_id=123,
        sizes=(3,))

    # Проверка основных кнопок
    assert any(btn.text == "❌ Удалить" for row in keyboard.inline_keyboard for btn in row)
    assert any(btn.text == "➖" for row in keyboard.inline_keyboard for btn in row)
    assert any(btn.text == "➕" for row in keyboard.inline_keyboard for btn in row)

    # Проверка пагинации
    next_btn = next(btn for row in keyboard.inline_keyboard for btn in row if btn.text == "➡️")
    next_data = MenuCallBack.unpack(next_btn.callback_data)
    assert next_data.page == 4

    # Проверка дополнительных кнопок
    assert any(btn.text == "🏠Меню" for row in keyboard.inline_keyboard for btn in row)
    assert any(btn.text == "Оформление 🚀" for row in keyboard.inline_keyboard for btn in row)


def test_cart_without_page():
    keyboard = get_user_cart_btn(
        level=2,
        page=None,
        pagination_btn=None,
        product_id=None,
        sizes=(1,)
    )

    assert len(keyboard.inline_keyboard) == 1
    assert keyboard.inline_keyboard[0][0].text == "🏠Обратно в меню"


@pytest.mark.parametrize("action,expected_page", [
    ("next", 4),
    ("prev", 2),
    ("invalid", None)  # Игнорируем некорректные действия
])
def test_pagination_actions(action, expected_page):
    keyboard = get_user_cart_btn(
        level=2,
        page=3,
        pagination_btn={f"Btn": action},
        product_id=123,
    )

    btns = [btn for row in keyboard.inline_keyboard for btn in row if btn.text == "Btn"]
    if action in {"next", "prev"}:
        assert len(btns) == 1
        data = MenuCallBack.unpack(btns[0].callback_data)
        assert data.page == expected_page
    else:
        assert len(btns) == 0


def test_edge_btn_cart_cases():
    # Тест с page=0 (минимальная допустимая страница)
    keyboard = get_user_cart_btn(
        level=0,
        page=0,
        pagination_btn={"⬅️": "prev"},
        product_id=0,
    )

    # Проверяем, что кнопка "⬅️" отсутствует (так как page-1 = -1 недопустимо)
    prev_btns = [btn for row in keyboard.inline_keyboard for btn in row if btn.text == "⬅️"]
    assert len(prev_btns) == 0, "Кнопка '⬅️' не должна отображаться при page=0"

    # Пустая пагинация
    keyboard = get_user_cart_btn(
        level=2,
        page=1,
        pagination_btn={},
        product_id=123,
    )
    assert len(keyboard.inline_keyboard) == 2  # Управление + дополнительные кнопки


# Тесты для get_user_catalog_btn

class MocksCategory:
    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name


def test_catalog_keyboard_basic():
    categories = [
        MockCategory(1, "Конфеты"),
        MockCategory(2, "Шоколад")
    ]
    keyboard = get_user_catalog_btn(
        level=2,
        categories=categories,
        sizes=(2,)
    )

    assert isinstance(keyboard, InlineKeyboardMarkup)

    # Проверка обязательных кнопок
    back_btn = next(btn for row in keyboard.inline_keyboard for btn in row if btn.text == "◀️Вернутся")
    back_data = MenuCallBack.unpack(back_btn.callback_data)
    assert back_data.level == 1
    assert back_data.menu_name == "main"

    cart_btn = next(btn for row in keyboard.inline_keyboard for btn in row if btn.text == "Корзина 🛒")
    cart_data = MenuCallBack.unpack(cart_btn.callback_data)
    assert cart_data.level == 3

    # Проверка кнопок категорий
    category_btns = [btn for row in keyboard.inline_keyboard for btn in row if btn.text in {"Конфеты", "Шоколад"}]
    assert len(category_btns) == 2
    assert all(
        MenuCallBack.unpack(btn.callback_data).category in {1, 2}
        for btn in category_btns
    )


def test_catalog_sizes():
    categories = [MockCategory(i, f"Cat{i}") for i in range(4)]
    keyboard = get_user_catalog_btn(
        level=1,
        categories=categories,
        sizes=(3, 1)
    )

    # 3 кнопки в первом ряду (основные + 1 категория)
    # 1 кнопка во втором ряду (оставшиеся категории)
    assert len(keyboard.inline_keyboard[0]) == 3
    assert len(keyboard.inline_keyboard[1]) == 1


def test_empty_btn_categories():
    keyboard = get_user_catalog_btn(
        level=2,
        categories=[],
        sizes=(2,)
    )

    # Только основные кнопки (2 в одном ряду)
    assert len(keyboard.inline_keyboard) == 1
    assert len(keyboard.inline_keyboard[0]) == 2


def test_edge_btn_catalog_cases():
    # Категория с некорректным ID
    categories = [MockCategory(None, "Invalid")]
    keyboard = get_user_catalog_btn(
        level=2,
        categories=categories,
        sizes=(2,)
    )

    # Кнопка должна быть создана, но category=None
    category_btn = next(btn for row in keyboard.inline_keyboard for btn in row if btn.text == "Invalid")
    assert MenuCallBack.unpack(category_btn.callback_data).category is None
