from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from typing_extensions import Optional


# Функция для создания клавиатуры для Telegram бота
# с заданными кнопками и настройками.
def get_keyboard(
        *btn: str,
        placeholder: Optional[str] = None,
        request_contact: Optional[int] = None,
        request_location: Optional[int] = None,
        sizes: tuple[int, ...] = (2,),
) -> ReplyKeyboardMarkup:
    """
    Функция для создания клавиатуры для Telegram бота
     с заданными кнопками и настройками.

    Параметры:
    - *btn: список строк, каждая из которых является текстом кнопки.
    - placeholder: (необязательный)
     строка для плейсхолдера в поле ввода.
    - request_contact: (необязательный)
     индекс кнопки, при нажатии на которую запрашивается контакт.
    - request_location: (необязательный)
     индекс кнопки, при нажатии на которую запрашивается локация.
    - sizes: кортеж целых чисел, определяющий расположение кнопок
     (количество кнопок в каждом ряду).

    Пример использования:
    get_keyboard("Меню",
        "О магазине",
        "Варианты оплаты",
        "Варианты доставки",
        "Отправить номер телефона",
        placeholder="Что вас интересует?",
        request_contact=4,
        sizes=(2, 2, 1)
    """
    # Создаем экземпляр билдера для создания клавиатуры
    keyboard = ReplyKeyboardBuilder()
    # Перебираем переданные кнопки,
    # используя enumerate для получения индекса кнопки
    for index, text in enumerate(btn):
        # Если задан параметр request_contact и
        # его значение совпадает с индексом кнопки,
        # создаем кнопку, которая запрашивает контакт пользователя при нажатии
        if request_contact is not None and request_contact == index:
            keyboard.add(KeyboardButton(text=text, request_contact=True))
        # Если задан параметр request_location
        # и его значение совпадает с индексом кнопки,
        # создаем кнопку, которая запрашивает
        # местоположение пользователя при нажатии
        elif request_location is not None and request_location == index:
            keyboard.add(KeyboardButton(text=text, request_location=True))
        # Если ни одно из условий не выполнено,
        # добавляем обычную кнопку с текстом
        else:
            keyboard.add(KeyboardButton(text=text))
    # Метод adjust расставляет кнопки
    # по рядам согласно переданным размерам (sizes),
    # а as_markup возвращает итоговую клавиатуру
    # в виде разметки с параметрами:
    # - resize_keyboard: автоматическое изменение размера клавиатуры для
    # удобства пользователя
    # - input_field_placeholder: плейсхолдер для поля ввода, если он указан
    return keyboard.adjust(*sizes).as_markup(  # type: ignore
        resize_keyboard=True, input_field_placeholder=placeholder
    )
