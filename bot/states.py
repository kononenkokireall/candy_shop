# Состояния для работы с ботом
from aiogram.fsm.state import State, StatesGroup


class OrderProcess(StatesGroup):
    """
    Состояния для процесса взаимодействия с ботом
    """
    Registration = State()  # Регистрация пользователя
    Greeting = State()  # Приветствие
    SelectItem = State()  # Выбор товара
    Payment = State()  # Выбор способа оплаты
    Confirmation = State()  # Потверждение заказа
