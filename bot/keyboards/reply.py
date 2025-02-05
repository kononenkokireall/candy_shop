from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# Функция создания динамической клавиатуры
def get_keyboard(
        *btn: str,  # Переменное количество кнопок в виде строк
        placeholder: str = None,  # Текст-заполнитель для строки ввода (input placeholder)
        request_contact: int = None,  # Индекс кнопки, запрашивающей контакт пользователя
        request_location: int = None,  # Индекс кнопки, запрашивающей местоположение пользователя
        sizes: tuple[int] = (2,),  # Размеры строк для кнопок (по умолчанию по 2 кнопки в строке)
):
    """
    Создание ReplyKeyboard с передачей параметров для кнопок.

    Parameters:
        btn (str): Список текстов для кнопок.
        placeholder (str): placeholder текстового поля.
        request_contact (int): Индекс кнопки, которая запрашивает контакт.
        request_location (int): Индекс кнопки, которая запрашивает местоположение.
        sizes (tuple[int]): Количество кнопок в строках.

    Returns:
        ReplyKeyboardMarkup: Настроенная клавиатура.
    """

    keyboard = ReplyKeyboardBuilder()  # Создаем генератор клавиатуры

    # Добавляем кнопки на клавиатуру
    for index, text in enumerate(btn, start=0):  # Перебираем переданные кнопки с индексами
        # Если индекс совпадает с request_contact, добавляем кнопку запроса контакта
        if request_contact is not None and request_contact == index:
            keyboard.add(KeyboardButton(text=text, request_contact=True))
        # Если индекс совпадает с request_location, добавляем кнопку запроса локации
        elif request_location is not None and request_location == index:
            keyboard.add(KeyboardButton(text=text, request_location=True))
        # Иначе, добавляем стандартную кнопку
        else:
            keyboard.add(KeyboardButton(text=text))

    # Настраиваем кнопки по строкам согласно параметру sizes
        reply_markup = keyboard.adjust(*sizes).as_markup(
            resize_keyboard=True,  # Уменьшаем размер клавиатуры для компактного отображения
            input_field_placeholder=placeholder  # Устанавливаем placeholder, если он указан
        )
        return reply_markup
