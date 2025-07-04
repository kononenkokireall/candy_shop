# Состояния для работы с ботом
from aiogram.fsm.state import State, StatesGroup


# Состояния для процесса взаимодействия с ботом
class OrderProcess(StatesGroup):
    """Состояния для процесса взаимодействия с ботом"""
    NAME = State()  # Этап регистрации (ввод имени)
    DESCRIPTION = State()  # Этап описания товара
    CATEGORY = State()  # Этап выбора категории
    PRICE = State()  # Этап Выбора способа оплаты
    QUANTITY = State() # Этап Выбора добавления цены
    ADD_IMAGES = State()  # Этап загрузки фото

    product_for_change = None

    TEXTS = {
        'OrderProcess:NAME': 'Введите название заново:',
        'OrderProcess:DESCRIPTION': 'Введите описание заново:',
        'OrderProcess:CATEGORY': 'Выберете категорию заново:',
        'OrderProcess:PRICE': 'Введите стоимость заново:',
        'OrderProcess:QUANTITY': 'Введите количество товара',
        'OrderProcess:ADD_IMAGES': 'Добавьте изображение меньше размером:',
    }


# Класс состояний FSM для загрузки баннеров через админ-панель
class AddBanner(StatesGroup):
    IMAGE = State()
