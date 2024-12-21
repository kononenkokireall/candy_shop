# Приветствие и регистрация пользователей
from aiogram.types import Message
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from keyboards import main_menu_keyboard, catalog_keyboard
from states import OrderProcess

# Создаем маршрутезатор
router = Router()


@router.message(Command('start'))
async def cmd_start(message: Message, state: FSMContext):
    """
    Обработчик команды /start.
    Приветствует пользователя и запускает процесс регистрации.
    """
    # Проверяем, зарегистрирован ли пользователь
    user_data = await state.get_data()
    if "name" in user_data:
        user_name = user_data["name"]
        await message.answer(
            f"С возвращением, {user_name}! Чем могу помочь?",
            reply_markup=main_menu_keyboard()
        )
    # Устанавливаем состояние регистрации
    await state.set_state(OrderProcess.Registration)
    await message.answer("Привет! Пожалуйста, зарегистрируйтесь. Как вас зовут?",
                         reply_markup=main_menu_keyboard())


@router.message(OrderProcess.Registration)
async def user_registration(message: Message, state: FSMContext):
    """ 
    Обрабатывает ввод имени пользователя.
    Сохраняет имя в состоянии и переводит пользователя на следующий шаг.
    """
    user_name = message.text.strip()
    if len(user_name) < 2 or not user_name.isalpha():
        await message.answer("""Имя слишком короткое или содержит 
                             недопустимые символы Пожалуйста, введите корректное имя.""")
        return
    # Сохраняем данные(Имя) пользователя в состоянии
    await state.update_data(name=user_name)

    # Переводим пользователя на следующий шаг
    await state.set_state(OrderProcess.Greeting)
    await message.answer(f"Рад с вами познакомиться, {user_name}! Чем могу помочь?",
                         reply_markup=catalog_keyboard())
