# Состояния для работы с ботом
from aiogram.fsm.state import State, StatesGroup


class OrderProcess(StatesGroup):

    """Состояния для процесса взаимодействия с ботом"""
    NAME = State() # Этап регистрации (ввод имени)
    DESCRIPTION = State() # Этап описания товара
    CATEGORY = State() # Этап выбора категории
    PRICE = State()  # Этап Выбора способа оплаты
    ADD_IMAGES = State() # Этап загрузки фото

    product_for_change = None

    TEXTS = {
        'OrderProcess:name': 'Введите название заново:',
        'OrderProcess:description': 'Введите описание заново:',
        'OrderProcess:price': 'Введите стоимость заново:',
        'OrderProcess:add_images': 'Добавьте изображение меньше размером:',
    }

class AddBanner(StatesGroup):
    IMAGE = State()
