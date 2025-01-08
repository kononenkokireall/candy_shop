# Состояния для работы с ботом
from aiogram.fsm.state import State, StatesGroup


class OrderProcess(StatesGroup):
    """Состояния для процесса взаимодействия с ботом"""
    Registration = State() # Этап регистрации (ввод имени)
    SelectCity = State()  # Этап Выбора города
    SelectItem = State()  # Этап Выбора товара
    Payment = State()  # Этап Выбора способа оплаты
    Confirmation = State()  # Подтверждение заказа
