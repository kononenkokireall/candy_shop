# Состояния для работы с ботом
from aiogram.fsm.state import State, StatesGroup


class OrderProcess(StatesGroup):
    """Состояния для процесса взаимодействия с ботом"""
    name = State() # Этап регистрации (ввод имени)
    description = State() # Этап описания товара
    payment = State()  # Этап Выбора способа оплаты
    add_images = State() # Этап загрузки фото

    texts = {
        'OrderProcess:name': 'Введите название заново:',
        'OrderProcess:description': 'Введите описание заново:',
        'OrderProcess:payment': 'Введите стоимость заново:',
        'OrderProcess:add_images': 'Добавьте изображение меньше размером:',
    }
