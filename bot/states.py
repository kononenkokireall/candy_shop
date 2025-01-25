# Состояния для работы с ботом
from aiogram.fsm.state import State, StatesGroup


class OrderProcess(StatesGroup):

    """Состояния для процесса взаимодействия с ботом"""
    name = State() # Этап регистрации (ввод имени)
    description = State() # Этап описания товара
    category = State() # Этап выбора категории
    price = State()  # Этап Выбора способа оплаты
    add_images = State() # Этап загрузки фото

    product_for_change = None

    texts = {
        'OrderProcess:name': 'Введите название заново:',
        'OrderProcess:description': 'Введите описание заново:',
        'OrderProcess:price': 'Введите стоимость заново:',
        'OrderProcess:add_images': 'Добавьте изображение меньше размером:',
    }

class AddBanner(StatesGroup):
    image = State()
