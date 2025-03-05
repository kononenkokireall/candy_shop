import logging
from unittest.mock import AsyncMock, patch, Mock

import pytest
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery, PhotoSize
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Order
from handlers.admin_events.admin_main import (
    admin_features,
    ADMIN_KB,
    cancel_handler,
    back_step_handler,
    add_product,
    add_image2,
    change_product_callback,
    add_name,
    add_description,
    starring_at_product,
    add_price,
    add_banner,
    add_image,
    delete_product_callback,
    confirm_order_handler,
    cancel_order_handler
)
from keyboards.linline_admin import OrderAction
from states.states import OrderProcess, AddBanner

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_admin_features_send_correct_message_and_kb():
    """Проверяем, что на команду /admin отправляется правильное сообщение с клавиатурой."""
    # Arrange
    mock_message = AsyncMock(spec=Message)
    mock_message.text = "/admin"

    # Act
    await admin_features(mock_message)

    # Assert
    # Проверяем, что ответ содержит правильный текст и клавиатуру
    mock_message.answer.assert_awaited_once_with(
        text="Что хотите сделать?",
        reply_markup=ADMIN_KB,
    )


@pytest.mark.asyncio
async def test_admin_features_ignore_non_admin_command():
    """Проверяем, что обработчик не реагирует на другие команды."""
    mock_message = AsyncMock(spec=Message)
    mock_message.text = "/help"  # Неверная команда

    # Если обработчик зарегистрирован через фильтр Command("admin"), этот тест можно пропустить.
    # Либо добавить проверку, что answer не вызывался:
    with pytest.raises(AssertionError):
        await admin_features(mock_message)
        mock_message.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_cancel_handler_with_state_and_product():
    """Проверка сброса состояния и product_for_change при их наличии."""
    # Arrange
    message = AsyncMock(spec=Message)
    state = AsyncMock(spec=FSMContext)
    state.get_state.return_value = "active_state"

    # Act
    with patch.object(OrderProcess, "product_for_change", "test_product"):
        await cancel_handler(message, state)

        # Assert: product_for_change сброшен
        assert OrderProcess.product_for_change is None

    # Assert: состояние очищено, сообщение отправлено
    state.clear.assert_awaited_once()
    message.answer.assert_awaited_once_with(
        "Действия отменены",
        reply_markup=ADMIN_KB
    )


@pytest.mark.asyncio
async def test_cancel_handler_with_state_no_product():
    """Проверка сброса состояния без product_for_change."""
    message = AsyncMock()
    state = AsyncMock()
    state.get_state.return_value = "active_state"

    # Act
    with patch.object(OrderProcess, "product_for_change", None):
        await cancel_handler(message, state)

    # Assert
    state.clear.assert_awaited_once()
    message.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_cancel_handler_no_state():
    """Проверка отсутствия действий при неактивном состоянии."""
    message = AsyncMock()
    state = AsyncMock()
    state.get_state.return_value = None  # Состояние отсутствует

    # Act
    with patch.object(OrderProcess, "product_for_change", "test_product"):
        await cancel_handler(message, state)

        # Assert: product_for_change не изменен
        assert OrderProcess.product_for_change == "test_product"

    # Assert: состояние не очищалось, сообщение не отправлено
    state.clear.assert_not_awaited()
    message.answer.assert_not_awaited()


@pytest.mark.asyncio
async def test_cancel_handler_case_insensitive():
    """Проверка реакции на текст 'ОТМЕНА' (верхний регистр)."""
    # Тест зависит от фильтров роутера. Для изоляции можно замокать F.text:
    message = AsyncMock()
    message.text = "ОТМЕНА"

    with patch("your_module.F.text.casefold") as mock_casefold:
        mock_casefold.__eq__.return_value = True
        await cancel_handler(message, AsyncMock())
        message.answer.assert_awaited()


@pytest.mark.asyncio
async def test_back_step_handler_on_first_step():
    """Проверка поведения при состоянии NAME (первый шаг)."""
    # Arrange
    message = AsyncMock(spec=Message)
    state = AsyncMock(spec=FSMContext)
    state.get_state.return_value = OrderProcess.NAME.state  # Текущее состояние — первый шаг

    # Act
    await back_step_handler(message, state)

    # Assert
    message.answer.assert_awaited_once_with(
        'Предыдущего шага нет, или введите название товара или напишите "отмена"'
    )
    state.set_state.assert_not_awaited()  # Состояние не меняется


@pytest.mark.asyncio
async def test_back_step_handler_not_first_step():
    """Проверка возврата на предыдущий шаг."""
    # Arrange
    message = AsyncMock()
    state = AsyncMock()

    # Задаем текущее состояние как второе в списке
    states = [Mock(state="state1"), Mock(state="state2")]
    with patch.object(OrderProcess, "__all_states__", states):
        state.get_state.return_value = "state2"  # Текущее состояние
        prev_state = states[0]  # Ожидаемое предыдущее состояние

        # Act
        await back_step_handler(message, state)

        # Assert
        state.set_state.assert_awaited_once_with(prev_state.state)
        message.answer.assert_awaited_once_with(
            "Ок, вы вернулись к прошлому шагу \n"
            f"{OrderProcess.TEXTS[prev_state.state]}"
        )


@pytest.mark.asyncio
async def test_back_step_handler_case_insensitive():
    """Проверка регистрированных независимости текста 'назад'."""
    # Тест зависит от фильтров роутера. Пример проверки через mock F.text:
    message = AsyncMock(text="НаЗаД")
    state = AsyncMock()
    state.get_state.return_value = "some_state"

    with patch("your_module.F.text.casefold") as mock_casefold:
        mock_casefold.__eq__.return_value = True
        await back_step_handler(message, state)
        state.set_state.assert_awaited()


@pytest.mark.asyncio
async def test_back_step_handler_state_order():
    """Проверка корректного перебора состояний."""
    # Arrange
    message = AsyncMock()
    state = AsyncMock()

    # Создаем список из 3 состояний
    states = [
        Mock(state="state1"),
        Mock(state="state2"),
        Mock(state="state3")
    ]

    with patch.object(OrderProcess, "__all_states__", states):
        # Текущее состояние — третье в списке
        state.get_state.return_value = "state3"

        # Act
        await back_step_handler(message, state)

        # Assert: предыдущее состояние — второе
        state.set_state.assert_awaited_once_with("state2")


@pytest.mark.asyncio
async def test_add_product_correct_trigger():
    """Проверка реакции на корректный триггер: текст 'Добавить товар' и состояние None."""
    # Arrange
    mock_message = AsyncMock(spec=Message)
    mock_message.text = "Добавить товар"
    mock_state = AsyncMock(spec=FSMContext)
    mock_state.get_state.return_value = None  # Состояние FSM отсутствует

    # Act
    await add_product(mock_message, mock_state)

    # Assert
    mock_message.answer.assert_awaited_once_with(
        "Введите название товара",
        reply_markup=ReplyKeyboardRemove(),
    )
    mock_state.set_state.assert_awaited_once_with(OrderProcess.NAME)


@pytest.mark.asyncio
async def test_add_product_ignore_wrong_text():
    """Проверка игнорирования некорректного текста (например, 'Добавить')."""
    mock_message = AsyncMock(text="Добавить")
    mock_state = AsyncMock()
    mock_state.get_state.return_value = None

    # Обработчик не должен вызываться (тест зависит от фильтров роутера)
    # Для проверки через mock:
    with patch("your_module.F.text") as mock_filter:
        mock_filter.__eq__.return_value = False
        await add_product(mock_message, mock_state)
        mock_message.answer.assert_not_awaited()


@pytest.mark.asyncio
async def test_add_product_ignore_non_none_state():
    """Проверка игнорирования при активном состоянии FSM."""
    mock_message = AsyncMock(text="Добавить товар")
    mock_state = AsyncMock()
    mock_state.get_state.return_value = "some_state"  # Состояние не None

    # Обработчик не должен вызываться
    await add_product(mock_message, mock_state)
    mock_message.answer.assert_not_awaited()
    mock_state.set_state.assert_not_awaited()


@pytest.mark.asyncio
async def test_reply_markup_is_removed():
    """Проверка, что reply_markup — это ReplyKeyboardRemove."""
    mock_message = AsyncMock(text="Добавить товар")
    mock_state = AsyncMock(get_state=Mock(return_value=None))

    await add_product(mock_message, mock_state)

    # Проверяем тип reply_markup
    reply_markup = mock_message.answer.call_args.kwargs.get("reply_markup")
    assert isinstance(reply_markup, ReplyKeyboardRemove)


@pytest.mark.asyncio
async def test_admin_features_with_categories():
    """Проверка корректной работы при наличии категорий."""
    # Arrange
    mock_message = AsyncMock(spec=Message)
    mock_message.text = "Ассортимент"
    mock_session = AsyncMock(spec=AsyncSession)

    # Мокируем категории
    mock_categories = [
        Mock(id=1, name="Электроника"),
        Mock(id=2, name="Одежда"),
    ]

    # Мокируем ORM-функцию и генератор кнопок
    with patch(
            "your_module.orm_get_categories",
            return_value=mock_categories) as mock_get_cat, \
            patch("your_module.get_callback_btn",
                  return_value="keyboard") as mock_btn_gen:
        # Act
        await admin_features(mock_message, mock_session)

        # Assert
        # Проверка вызова orm_get_categories
        mock_get_cat.assert_awaited_once_with(mock_session)

        # Проверка генерации кнопок
        expected_buttons = {
            "Электроника": "category_1",
            "Одежда": "category_2",
        }
        mock_btn_gen.assert_called_once_with(btn=expected_buttons)

        # Проверка отправки сообщения
        mock_message.answer.assert_awaited_once_with(
            "Выберите категорию",
            reply_markup="keyboard",
        )


@pytest.mark.asyncio
async def test_admin_features_empty_categories():
    """Проверка обработки пустого списка категорий."""
    mock_message = AsyncMock(text="Ассортимент")
    mock_session = AsyncMock()

    with patch(
            "your_module.orm_get_categories", return_value=[]), \
            patch(
                "your_module.get_callback_btn",
                return_value="empty_keyboard") as mock_btn:
        await admin_features(mock_message, mock_session)

        # Проверка вызова с пустым словарем кнопок
        mock_btn.assert_called_once_with(btn={})
        mock_message.answer.assert_awaited_once_with(
            "Выберите категорию",
            reply_markup="empty_keyboard",
        )

@pytest.mark.asyncio
async def test_add_image2_correct_trigger():
    """Проверка реакции на корректный триггер и корректной работы."""
    # Arrange
    mock_message = AsyncMock(spec=Message)
    mock_message.text = "Добавить/Изменить баннер"
    mock_state = AsyncMock(spec=FSMContext)
    mock_session = AsyncMock(spec=AsyncSession)
    pages = [Mock(name="Главная"), Mock(name="О нас")]

    with patch(
            "your_module.orm_get_info_pages",
            return_value=pages) as mock_get_pages:
        # Act
        await add_image2(mock_message, mock_state, mock_session)

        # Assert
        # Проверка получения страниц
        mock_get_pages.assert_awaited_once_with(mock_session)

        # Проверка сообщения
        expected_text = (
            "Отправьте фото баннера.\n"
            "В описании укажите для какой страницы:\n"
            "Главная, О нас"
        )
        mock_message.answer.assert_awaited_once_with(expected_text)

        # Проверка состояния
        mock_state.set_state.assert_awaited_once_with(AddBanner.IMAGE)

@pytest.mark.asyncio
async def test_add_image2_empty_pages():
    """Проверка обработки пустого списка страниц."""
    mock_message = AsyncMock(text="Добавить/Изменить баннер")
    mock_session = AsyncMock()

    with patch("your_module.orm_get_info_pages", return_value=[]):
        await add_image2(mock_message, AsyncMock(), mock_session)

        # Проверка сообщения без страниц
        expected_text = (
            "Отправьте фото баннера.\n"
            "В описании укажите для какой страницы:\n"
            ""
        )
        mock_message.answer.assert_awaited_once_with(expected_text.strip())

@pytest.mark.asio
async def test_add_image2_ignore_non_none_state():
    """Проверка игнорирования при активном состоянии FSM."""
    mock_message = AsyncMock(text="Добавить/Изменить баннер")
    mock_state = AsyncMock(get_state=AsyncMock(return_value="some_state"))

    await add_image2(mock_message, mock_state, AsyncMock())

    # Проверка, что сообщение не отправлено и состояние не изменено
    mock_message.answer.assert_not_awaited()
    mock_state.set_state.assert_not_awaited()

@pytest.mark.asyncio
async def test_add_image2_ignore_wrong_text():
    """Проверка игнорирования некорректного текста."""
    mock_message = AsyncMock(text="Добавить товар")
    mock_session = AsyncMock()

    # Обработчик не должен вызываться (зависит от фильтров роутера)
    # Проверка через mock:
    with patch("your_module.F.text") as mock_filter:
        mock_filter.__eq__.return_value = False
        await add_image2(mock_message, AsyncMock(), mock_session)
        mock_message.answer.assert_not_awaited()


@pytest.mark.asyncio
async def test_change_product_callback_valid_data():
    """Проверка корректной обработки callback с валидным product_id."""
    # Arrange
    callback = AsyncMock(spec=CallbackQuery)
    callback.data = "change_123"  # Валидный product_id
    state = AsyncMock(spec=FSMContext)
    session = AsyncMock(spec=AsyncSession)
    mock_product = Mock(id=123, name="Test Product")

    # Мокируем получение товара
    with patch(
            "your_module.orm_get_product",
            return_value=mock_product) as mock_get_product:
        # Act
        await change_product_callback(callback, state, session)

        # Assert
        # Проверка извлечения product_id
        assert callback.data.split("_")[-1] == "123"

        # Проверка запроса товара из БД
        mock_get_product.assert_awaited_once_with(session, 123)

        # Проверка сохранения товара
        assert OrderProcess.product_for_change == mock_product

        # Проверка отправки сообщений
        callback.answer.assert_awaited_once()
        callback.message.answer.assert_awaited_once_with(
            "Введите название товара",
            reply_markup=types.ReplyKeyboardRemove()
        )

        # Проверка установки состояния FSM
        state.set_state.assert_awaited_once_with(OrderProcess.NAME)

@pytest.mark.asyncio
async def test_change_product_callback_invalid_product_id():
    """Обработка callback с невалидным product_id (не число)."""
    callback = AsyncMock(data="change_invalid")
    session = AsyncMock()

    with pytest.raises(ValueError, match="invalid literal for int()"):
        await change_product_callback(callback, AsyncMock(), session)

    # Проверка, что товар не сохранялся
    assert OrderProcess.product_for_change is None

@pytest.mark.asyncio
async def test_change_product_callback_product_not_found():
    """Обработка случая, когда товар не найден в БД."""
    callback = AsyncMock(data="change_456")
    session = AsyncMock()

    with patch("your_module.orm_get_product", return_value=None):
        await change_product_callback(callback, AsyncMock(), session)

        # Проверка, что product_for_change не установлен
        assert OrderProcess.product_for_change is None

        # Проверка отправки сообщения об ошибке (если есть)
        # callback.message.answer.assert_called_with("Товар не найден")

@pytest.mark.asyncio
async def test_change_product_callback_ignore_non_change_data():
    """Проверка игнорирования callback с некорректным data."""
    callback = AsyncMock(data="other_data_123")
    session = AsyncMock()

    # Если обработчик зарегистрирован через фильтр F.data.startswith("change_"), этот тест можно пропустить
    # Или проверить через mock:
    with patch("your_module.F.data.startswith") as mock_filter:
        mock_filter.return_value = False
        await change_product_callback(callback, AsyncMock(), session)
        callback.answer.assert_not_awaited()

@pytest.mark.asyncio
async def test_add_name_dot_with_product_for_change():
    """Ввод точки при наличии product_for_change: сохраняется старое название."""
    # Arrange
    mock_message = AsyncMock(spec=Message)
    mock_message.text = "."
    mock_state = AsyncMock(spec=FSMContext)
    OrderProcess.product_for_change = Mock(name="Old Product")

    # Act
    await add_name(mock_message, mock_state)

    # Assert
    mock_state.update_data.assert_awaited_once_with(name="Old Product")
    mock_message.answer.assert_awaited_once_with("Введите описание товара")
    mock_state.set_state.assert_awaited_once_with(OrderProcess.DESCRIPTION)
    OrderProcess.product_for_change = None  # Сброс

@pytest.mark.asyncio
async def test_add_name_valid_new_name():
    """Ввод нового названия с допустимой длиной (5 символов)."""
    mock_message = AsyncMock(text="Valid")
    mock_state = AsyncMock()

    await add_name(mock_message, mock_state)

    mock_state.update_data.assert_awaited_once_with(name="Valid")
    mock_message.answer.assert_awaited_once_with("Введите описание товара")
    mock_state.set_state.assert_awaited_once_with(OrderProcess.DESCRIPTION)

@pytest.mark.asyncio
async def test_add_name_invalid_length_short():
    """Ввод слишком короткого названия (4 символа)."""
    mock_message = AsyncMock(text="1234")
    mock_state = AsyncMock()

    await add_name(mock_message, mock_state)

    mock_message.answer.assert_awaited_once_with(
        "Название товара не должно превышать 150 символов\n"
        "или быть менее 5 ти символов. \n"
        "Введите заново"
    )
    mock_state.set_state.assert_not_awaited()

@pytest.mark.asyncio
async def test_add_name_invalid_length_long():
    """Ввод слишком длинного названия (151 символ)."""
    mock_message = AsyncMock(text="a" * 151)
    mock_state = AsyncMock()

    await add_name(mock_message, mock_state)

    mock_message.answer.assert_awaited_once_with(
        "Название товара не должно превышать 150 символов\n"
        "или быть менее 5 ти символов. \n"
        "Введите заново"
    )
    mock_state.set_state.assert_not_awaited()

@pytest.mark.asyncio
async def test_add_name_dot_without_product_for_change():
    """Ввод точки без product_for_change: обрабатывается как ошибка длины."""
    mock_message = AsyncMock(text=".")
    mock_state = AsyncMock()
    OrderProcess.product_for_change = None  # Явно задаем отсутствие продукта

    await add_name(mock_message, mock_state)

    mock_message.answer.assert_awaited_once_with(
        "Название товара не должно превышать 150 символов\n"
        "или быть менее 5 ти символов. \n"
        "Введите заново"
    )
    mock_state.set_state.assert_not_awaited()

@pytest.mark.asyncio
async def test_add_description_dot_with_product():
    """Сохранение старого описания при вводе '.' и наличии product_for_change."""
    # Arrange
    mock_message = AsyncMock(spec=Message)
    mock_message.text = "."
    mock_state = AsyncMock(spec=FSMContext)
    mock_session = AsyncMock(spec=AsyncSession)
    OrderProcess.product_for_change = Mock(description="Old Description")

    # Мокируем категории
    mock_categories = [Mock(id=1, name="Электроника")]
    with patch("your_module.orm_get_categories", return_value=mock_categories), \
         patch("your_module.get_callback_btn", return_value="keyboard"):

        # Act
        await add_description(mock_message, mock_state, mock_session)

        # Assert
        mock_state.update_data.assert_awaited_once_with(description="Old Description")
        mock_message.answer.assert_any_call("Выберите категорию", reply_markup="keyboard")
        mock_state.set_state.assert_awaited_once_with(OrderProcess.CATEGORY)
    OrderProcess.product_for_change = None  # Сброс

@pytest.mark.asyncio
async def test_add_description_valid_text(mock_state=None):
    """Сохранение нового описания с длиной >=5 символов."""
    mock_message = AsyncMock(text="Valid Description (5+ символов)")
    mock_session = AsyncMock()
    mock_categories = [Mock(id=2, name="Одежда")]

    with patch("your_module.orm_get_categories", return_value=mock_categories), \
         patch("your_module.get_callback_btn") as mock_btn:

        await add_description(mock_message, AsyncMock(), mock_session)

        # Проверка сохранения данных
        mock_state.update_data.assert_awaited_once_with(description="Valid Description (5+ символов)")
        mock_btn.assert_called_once_with(btn={"Одежда": "2"})

@pytest.mark.asyncio
async def test_add_description_short_text():
    """Обработка слишком короткого описания (<=4 символов)."""
    mock_message = AsyncMock(text="1234")
    mock_state = AsyncMock()

    await add_description(mock_message, mock_state, AsyncMock())

    # Проверка сообщения об ошибке
    mock_message.answer.assert_awaited_once_with("Слишком короткое описание. \nВведите заново")
    mock_state.set_state.assert_not_awaited()

@pytest.mark.asyncio
async def test_add_description_empty_categories():
    """Проверка генерации кнопок при отсутствии категорий."""
    mock_message = AsyncMock(text="Valid text")
    mock_session = AsyncMock()

    with patch("your_module.orm_get_categories", return_value=[]), \
         patch("your_module.get_callback_btn") as mock_btn:

        await add_description(mock_message, AsyncMock(), mock_session)

        # Проверка вызова с пустым списком кнопок
        mock_btn.assert_called_once_with(btn={})

@pytest.mark.asyncio
async def test_add_description_ignore_non_description_state():
    """Функция не вызывается вне состояния DESCRIPTION."""
    # Тест зависит от фильтров роутера. Пример проверки через mock:
    mock_message = AsyncMock()
    with patch("your_module.StateFilter") as mock_filter:
        mock_filter.verify.return_value = False
        await add_description(mock_message, AsyncMock(), AsyncMock())
        mock_message.answer.assert_not_awaited()


@pytest.mark.asyncio
async def test_starring_at_product_success():
    """Успешная обработка callback с товарами в категории."""
    # Arrange
    callback = AsyncMock(spec=CallbackQuery)
    callback.data = "category_123"
    session = AsyncMock(spec=AsyncSession)

    # Мокируем товары
    mock_products = [
        Mock(
            id=1,
            name="Товар 1",
            description="Описание 1",
            price=100.0,
            image="image1.jpg"
        ),
        Mock(
            id=2,
            name="Товар 2",
            description="Описание 2",
            price=200.0,
            image="image2.jpg"
        )
    ]

    with patch("your_module.orm_get_products", return_value=mock_products) as mock_get, \
            patch("your_module.get_callback_btn", return_value="keyboard") as mock_btn:
        # Act
        await starring_at_product(callback, session)

        # Assert
        # Проверка получения товаров
        mock_get.assert_awaited_once_with(session, 123)

        # Проверка отправки карточек
        assert callback.message.answer_photo.await_count == 2

        # Проверка данных первого товара
        first_call = callback.message.answer_photo.await_args_list[0]
        assert first_call.kwargs["photo"] == "image1.jpg"
        assert "Товар 1" in first_call.kwargs["caption"]
        assert "100.0" in first_call.kwargs["caption"]
        mock_btn.assert_any_call(
            btn={"Удалить": "delete_1", "Изменить": "change_1"},
            sizes=(2,)
        )

        # Проверка финальных действий
        callback.answer.assert_awaited_once()
        callback.message.answer.assert_awaited_once_with("ОК, вот список товаров ⏫")


@pytest.mark.asyncio
async def test_starring_at_product_empty_products():
    """Обработка колбэка с пустой категорией."""
    callback = AsyncMock(data="category_456")
    session = AsyncMock()

    with patch("your_module.orm_get_products", return_value=[]):
        await starring_at_product(callback, session)

        # Проверка отсутствия отправленных фото
        callback.message.answer_photo.assert_not_awaited()
        # Проверка финального сообщения
        callback.message.answer.assert_awaited_once_with("ОК, вот список товаров ⏫")


@pytest.mark.asyncio
async def test_starring_at_product_invalid_category_id():
    """Нечисловой ID категории вызывает ошибку."""
    callback = AsyncMock(data="category_invalid")
    session = AsyncMock()

    with pytest.raises(ValueError):
        await starring_at_product(callback, session)


@pytest.mark.asyncio
async def test_starring_at_product_ignore_other_callbacks():
    """Игнорирование callback с некорректным префиксом."""
    callback = AsyncMock(data="other_data_123")
    session = AsyncMock()

    # Если обработчик зарегистрирован через фильтр, можно пропустить
    # или проверить через mock:
    with patch("your_module.F.data.startswith", return_value=False):
        await starring_at_product(callback, session)
        callback.answer.assert_not_awaited()


@pytest.mark.asyncio
async def test_add_price_dot_with_product_for_change():
    """Ввод '.' с существующим product_for_change: сохранение старой цены."""
    # Arrange
    mock_message = AsyncMock(spec=Message)
    mock_message.text = "."
    mock_state = AsyncMock(spec=FSMContext)
    OrderProcess.product_for_change = Mock(price=150.0)

    # Act
    await add_price(mock_message, mock_state)

    # Assert
    mock_state.update_data.assert_awaited_once_with(price=150.0)
    mock_message.answer.assert_awaited_once_with("Загрузите изображение товара")
    mock_state.set_state.assert_awaited_once_with(OrderProcess.ADD_IMAGES)
    OrderProcess.product_for_change = None  # Сброс

@pytest.mark.asyncio
async def test_add_price_dot_without_product_for_change():
    """Ввод '.' без product_for_change: ошибка валидации."""
    mock_message = AsyncMock(text=".")
    mock_state = AsyncMock()
    OrderProcess.product_for_change = None

    await add_price(mock_message, mock_state)

    # Проверка отправки ошибки
    mock_message.answer.assert_awaited_once_with("Введите корректное значение цены")
    mock_state.set_state.assert_not_awaited()

@pytest.mark.asyncio
async def test_add_price_valid_number():
    """Ввод корректного числа: сохранение цены и переход к следующему шагу."""
    mock_message = AsyncMock(text="200.5")
    mock_state = AsyncMock()

    await add_price(mock_message, mock_state)

    mock_state.update_data.assert_awaited_once_with(price="200.5")
    mock_message.answer.assert_awaited_once_with("Загрузите изображение товара")
    mock_state.set_state.assert_awaited_once_with(OrderProcess.ADD_IMAGES)

@pytest.mark.asyncio
async def test_add_price_invalid_input():
    """Ввод нечислового значения: отправка ошибки."""
    mock_message = AsyncMock(text="сто_рублей")
    mock_state = AsyncMock()

    await add_price(mock_message, mock_state)

    mock_message.answer.assert_awaited_once_with("Введите корректное значение цены")
    mock_state.update_data.assert_not_awaited()
    mock_state.set_state.assert_not_awaited()

@pytest.mark.asyncio
async def test_add_price_comma_decimal_separator():
    """Проверка обработки числа с запятой (должна быть ошибка)."""
    mock_message = AsyncMock(text="200,5")
    mock_state = AsyncMock()

    await add_price(mock_message, mock_state)

    mock_message.answer.assert_awaited_once_with("Введите корректное значение цены")
    mock_state.set_state.assert_not_awaited()


@pytest.mark.asyncio
async def test_add_banner_success():
    """Успешное добавление баннера с валидной подписью."""
    # Arrange
    mock_message = AsyncMock(spec=Message)
    mock_message.photo = [PhotoSize(file_id="photo1"), PhotoSize(file_id="photo2")]
    mock_message.caption = "main"  # Валидная подпись
    mock_session = AsyncMock(spec=AsyncSession)
    mock_state = AsyncMock(spec=FSMContext)

    # Мокируем страницы
    mock_pages = [Mock(name="main"), Mock(name="catalog")]
    with patch("your_module.orm_get_info_pages", return_value=mock_pages), \
         patch("your_module.orm_change_banner_image") as mock_change_banner:

        # Act
        await add_banner(mock_message, mock_state, mock_session)

        # Assert
        # Проверка извлечения file_id последнего фото
        assert mock_message.photo[-1].file_id == "photo2"

        # Проверка обновления баннера
        mock_change_banner.assert_awaited_once_with(
            session=mock_session,
            page_name="main",
            image_id="photo2"
        )

        # Проверка отправки подтверждения и очистки состояния
        mock_message.answer.assert_awaited_once_with("Баннер добавлен/изменен.")
        mock_state.clear.assert_awaited_once()

@pytest.mark.asyncio
async def test_add_banner_invalid_caption():
    """Некорректная подпись: страница не найдена."""
    mock_message = AsyncMock()
    mock_message.photo = [PhotoSize(file_id="photo1")]
    mock_message.caption = "invalid_page"
    mock_session = AsyncMock()
    mock_pages = [Mock(name="main"), Mock(name="catalog")]

    with patch("your_module.orm_get_info_pages", return_value=mock_pages):
        await add_banner(mock_message, AsyncMock(), mock_session)

        # Проверка отправки сообщения с примерами
        mock_message.answer.assert_awaited_once_with(
            "Введите нормальное название страницы, например:\nmain, catalog"
        )
        # Проверка, что БД не обновлялась
        mock_session.commit.assert_not_awaited()

@pytest.mark.asyncio
async def test_add_banner_empty_caption():
    """Отсутствие подписи (caption = None)."""
    mock_message = AsyncMock()
    mock_message.photo = [PhotoSize(file_id="photo1")]
    mock_message.caption = None  # Подпись отсутствует
    mock_pages = [Mock(name="main")]

    with patch("your_module.orm_get_info_pages", return_value=mock_pages):
        await add_banner(mock_message, AsyncMock(), AsyncMock())

        # Проверка запроса на ввод корректной подписи
        mock_message.answer.assert_awaited_once_with(
            "Введите нормальное название страницы, например:\nmain"
        )

@pytest.mark.asyncio
async def test_add_banner_trim_caption():
    """Подпись с пробелами: ' main ' -> 'main'."""
    mock_message = AsyncMock()
    mock_message.photo = [PhotoSize(file_id="photo1")]
    mock_message.caption = "  main  "  # Подпись с пробелами
    mock_pages = [Mock(name="main")]

    with patch("your_module.orm_get_info_pages", return_value=mock_pages), \
         patch("your_module.orm_change_banner_image") as mock_change_banner:

        await add_banner(mock_message, AsyncMock(), AsyncMock())

        # Проверка обработки подписи с trim()
        mock_change_banner.assert_awaited_once_with(
            session=AsyncMock(),
            page_name="main",
            image_id="photo1"
        )


@pytest.mark.asyncio
async def test_add_image_keep_old_image():
    """Сохранение старого изображения при вводе '.' и наличии product_for_change."""
    # Arrange
    mock_message = AsyncMock(spec=Message)
    mock_message.text = "."
    mock_state = AsyncMock(spec=FSMContext)
    mock_session = AsyncMock(spec=AsyncSession)
    OrderProcess.product_for_change = Mock(id=1, image="old_image.jpg")
    mock_state.get_data.return_value = {"name": "Test", "price": 100}

    # Act
    await add_image(mock_message, mock_state, mock_session)

    # Assert
    mock_state.update_data.assert_awaited_once_with(image="old_image.jpg")
    mock_session.commit.assert_awaited()
    mock_message.answer.assert_awaited_once_with("Товар добавлен/Изменен", reply_markup=ADMIN_KB)
    mock_state.clear.assert_awaited_once()
    assert OrderProcess.product_for_change is None

@pytest.mark.asyncio
async def test_add_image_new_photo():
    """Добавление нового товара с фото."""
    mock_message = AsyncMock()
    mock_message.photo = [PhotoSize(file_id="photo1"), PhotoSize(file_id="photo2")]
    mock_state = AsyncMock()
    mock_state.get_data.return_value = {"name": "New", "price": 200}
    OrderProcess.product_for_change = None

    with patch("your_module.orm_add_product") as mock_add:
        await add_image(mock_message, mock_state, AsyncMock())

        # Проверка сохранения file_id последнего фото
        mock_state.update_data.assert_awaited_once_with(image="photo2")
        mock_add.assert_awaited_once_with(AsyncMock(), {"name": "New", "price": 200, "image": "photo2"})
        mock_message.answer.assert_called_with("Товар добавлен/Изменен", reply_markup=ADMIN_KB)

@pytest.mark.asyncio
async def test_add_image_invalid_input():
    """Обработка некорректного ввода (текст не '.')."""
    mock_message = AsyncMock()
    mock_message.text = "invalid"
    mock_message.photo = None

    await add_image(mock_message, AsyncMock(), AsyncMock())

    mock_message.answer.assert_awaited_once_with("Отправьте фото пищи")
    assert OrderProcess.product_for_change is None

@pytest.mark.asyncio
async def test_add_image_database_error():
    """Обработка ошибки при сохранении в БД."""
    mock_message = AsyncMock(text=".")
    mock_message.photo = None
    mock_state = AsyncMock()
    OrderProcess.product_for_change = Mock()
    mock_state.get_data.return_value = {}

    # Мокируем исключение в ORM
    with patch("your_module.orm_update_product", side_effect=Exception("DB Error")) as mock_update:
        await add_image(mock_message, mock_state, AsyncMock())

        # Проверка отправки ошибки
        mock_message.answer.assert_awaited_once_with(
            "Ошибка: \nDB Error\nОбратись к разработчику",
            reply_markup=ADMIN_KB,
        )
        mock_state.clear.assert_awaited_once()
        assert OrderProcess.product_for_change is None


@pytest.mark.asyncio
async def test_delete_product_valid_id(orm_delete_order=None):
    """Корректное удаление товара с валидным ID."""
    # Arrange
    callback = AsyncMock(spec=CallbackQuery)
    callback.data = "delete_123"
    session = AsyncMock(spec=AsyncSession)

    # Act
    await delete_product_callback(callback, session)

    # Assert
    # Проверка извлечения ID
    assert callback.data.split("_")[-1] == "123"

    # Проверка вызова orm_delete_product
    orm_delete_order.assert_awaited_once_with(session, 123)

    # Проверка отправки подтверждений
    callback.answer.assert_awaited_once_with("Товар удален")
    callback.message.answer.assert_awaited_once_with("Товар удален!")


@pytest.mark.asyncio
async def test_delete_product_invalid_id():
    """Попытка удаления с нечисловым ID."""
    callback = AsyncMock(data="delete_invalid")
    session = AsyncMock()

    with pytest.raises(ValueError, match="invalid literal for int()"):
        await delete_product_callback(callback, session)

    # Проверка, что удаление не вызывалось
    orm_delete_product.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_product_ignore_non_delete_callback():
    """Игнорирование колбэков без префикса 'delete_'."""
    callback = AsyncMock(data="other_123")
    session = AsyncMock()

    # Если обработчик зарегистрирован через фильтр F.data.startswith("delete_"), тест можно пропустить
    with patch("your_module.F.data.startswith", return_value=False):
        await delete_product_callback(callback, session)
        callback.answer.assert_not_awaited()
        orm_delete_product.assert_not_awaited()


@pytest.mark.asyncio
async def test_confirm_order_success():
    """Успешное подтверждение заказа."""
    # Arrange
    callback = AsyncMock(spec=CallbackQuery)
    callback_data = Mock(spec=OrderAction, action="confirm", order_id=1)
    session = AsyncMock(spec=AsyncSession)
    mock_order = Mock(spec=Order, status="pending", user_id=123)

    # Мокируем session.get с блокировкой
    session.get.return_value = mock_order
    session.commit = AsyncMock()

    # Act
    await confirm_order_handler(callback, callback_data, session)

    # Assert
    session.get.assert_awaited_once_with(Order, 1, with_for_update=True)
    assert mock_order.status == "confirmed"
    session.commit.assert_awaited_once()
    callback.bot.send_message.assert_awaited_once_with(
        chat_id=123,
        text="🎉 <b>Ваш заказ подтвержден!</b>\n\n✅ Оплата прошла успешно\n📦 Забрать можно по адресу: ул. Примерная, 123",
        parse_mode="HTML"
    )
    callback.answer.assert_awaited_with("✅ Заказ подтвержден")


@pytest.mark.asyncio
async def test_order_not_found():
    """Заказ не найден в БД."""
    session = AsyncMock()
    session.get.return_value = None

    await confirm_order_handler(AsyncMock(), Mock(order_id=999), session)

    callback.answer.assert_awaited_with("🚨 Заказ не найден", show_alert=True)
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_order_already_confirmed():
    """Заказ уже подтвержден."""
    mock_order = Mock(status="confirmed")
    session = AsyncMock()
    session.get.return_value = mock_order

    await confirm_order_handler(AsyncMock(), Mock(order_id=1), session)

    callback.answer.assert_awaited_with("ℹ️ Заказ уже подтвержден")
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_notification_send_error():
    """Ошибка отправки уведомления пользователю."""
    mock_order = Mock(status="pending", user_id=123)
    session = AsyncMock()
    session.get.return_value = mock_order
    callback.bot.send_message.side_effect = Exception("Telegram API Error")

    await confirm_order_handler(AsyncMock(), Mock(order_id=1), session)

    logger.error.assert_called_with("Ошибка отправки уведомления: Telegram API Error")
    callback.answer.assert_awaited_with("✅ Заказ подтвержден")


@pytest.mark.asyncio
async def test_general_error_handling():
    """Обработка общей ошибки (например, ошибка коммита)."""
    session = AsyncMock()
    session.get.side_effect = Exception("DB Connection Error")

    await confirm_order_handler(AsyncMock(), Mock(order_id=1), session)

    logger.error.assert_called_with("Ошибка подтверждения: DB Connection Error", exc_info=True)
    session.rollback.assert_awaited_once()
    callback.answer.assert_awaited_with("🚨 Ошибка подтверждения заказа", show_alert=True)

@pytest.mark.asyncio
async def test_cancel_order_success():
    """Успешная отмена заказа."""
    # Arrange
    callback = AsyncMock(spec=CallbackQuery)
    callback_data = Mock(spec=OrderAction, action="cancel", order_id=1)
    session = AsyncMock(spec=AsyncSession)
    mock_order = Mock(spec=Order, status="pending", user_id=123)

    # Мокируем получение заказа с блокировкой
    session.get.return_value = mock_order
    session.commit = AsyncMock()

    # Act
    await cancel_order_handler(callback, callback_data, session)

    # Assert
    session.get.assert_awaited_once_with(Order, 1, with_for_update=True)
    assert mock_order.status == "cancelled"
    session.commit.assert_awaited_once()
    callback.bot.send_message.assert_awaited_once_with(
        chat_id=123,
        text=(
            "❌ <b>Заказ отменен</b>\n\n"
            "Администратор отменил ваш заказ. "
            "Для уточнения деталей свяжитесь с администратором."
        ),
        parse_mode="HTML"
    )
    callback.answer.assert_awaited_with("❌ Заказ отменен")

@pytest.mark.asyncio
async def test_order_not_found():
    """Попытка отмены несуществующего заказа."""
    session = AsyncMock()
    session.get.return_value = None

    await cancel_order_handler(AsyncMock(), Mock(order_id=999), session)

    callback.answer.assert_awaited_with("🚨 Заказ не найден", show_alert=True)
    session.commit.assert_not_awaited()

@pytest.mark.asyncio
async def test_order_already_cancelled():
    """Заказ уже отменен."""
    mock_order = Mock(status="cancelled")
    session = AsyncMock()
    session.get.return_value = mock_order

    await cancel_order_handler(AsyncMock(), Mock(order_id=1), session)

    callback.answer.assert_awaited_with("ℹ️ Заказ уже отменен")
    session.commit.assert_not_awaited()

@pytest.mark.asyncio
async def test_notification_send_error():
    """Ошибка отправки уведомления пользователю."""
    mock_order = Mock(status="pending", user_id=123)
    session = AsyncMock()
    session.get.return_value = mock_order
    callback.bot.send_message.side_effect = Exception("Telegram API Error")

    await cancel_order_handler(AsyncMock(), Mock(order_id=1), session)

    logger.error.assert_called_with("Ошибка отправки уведомления: Telegram API Error")
    callback.answer.assert_awaited_with("❌ Заказ отменен")

@pytest.mark.asyncio
async def test_general_error_handling():
    """Обработка общей ошибки (например, ошибка коммита)."""
    session = AsyncMock()
    session.get.side_effect = Exception("DB Connection Error")

    await cancel_order_handler(AsyncMock(), Mock(order_id=1), session)

    logger.error.assert_called_with("Ошибка отмены: DB Connection Error", exc_info=True)
    session.rollback.assert_awaited_once()
    callback.answer.assert_awaited_with("🚨 Ошибка отмены заказа", show_alert=True)