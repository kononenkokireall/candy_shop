# Состояния для работы с ботом
from aiogram.fsm.state import State, StatesGroup


class OrderProcess(StatesGroup):
    """Состояния для процесса взаимодействия с ботом"""
    NAME = State()  # Этап регистрации (ввод имени)
    DESCRIPTION = State()  # Этап описания товара
    CATEGORY = State()  # Этап выбора категории
    PRICE = State()  # Этап Выбора способа оплаты
    ADD_IMAGES = State()  # Этап загрузки фото

    product_for_change = None

    TEXTS = {
        'OrderProcess:NAME': 'Введите название заново:',
        'OrderProcess:DESCRIPTION': 'Введите описание заново:',
        'OrderProcess:PRICE': 'Введите стоимость заново:',
        'OrderProcess:ADD_IMAGES': 'Добавьте изображение меньше размером:',
    }


class AddBanner(StatesGroup):
    IMAGE = State()
