# Приветствие и регистрация пользователей
from aiogram.types import Message
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from keyboards import main_menu_keyboard, catalog_keyboard, city_selection_keyboard
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
    if "name" in user_data and "city" in user_data:
        user_name = user_data["name"]
        user_city = user_data["city"]
        await message.answer(
            f"""С возвращением, {user_name} из города {
                user_city}! Чем могу помочь?""",
            reply_markup=main_menu_keyboard()
        )
    else:
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

    # Переводим пользователя на следующий шаг: выбор города
    await state.set_state(OrderProcess.SelectCity)
    await message.answer(
        "Спасибо! Теперь выберете город, в котором вы находитесь:", reply_markup=city_selection_keyboard()
    )


@router.message(OrderProcess.SelectCity)
async def user_select_city(message: Message, state: FSMContext):
    """
    Обрабатывает выбор города пользователем.
    Сохраняет город в состоянии и завершает процесс регистрации.
    """
    user_city = message.text.strip()
    available_cities = ["Вроцлав", "Краков", "Варшаваю", "Познань"]

    if user_city not in available_cities:
        await message.answer("""Извините, этого города нет в списке.
                             Пожалуйста, выберете город из списка.""")
        return
    # Сохраняем данные(Город) пользователя в состоянии
    await state.update_data(city=user_city)

    # Переводим пользователя на следующий шаг: приветствие
    await state.set_state(OrderProcess.Greeting)
    user_data = await state.get_data()
    user_name = user_data["name"]
    await message.answer(
        f"Рад с Вами познакомиться, {user_name} из {user_city}! Чем могу помочь?", reply_markup=catalog_keyboard()
    )


@router.message(Command('change_city'))
async def cmd_change_city(message: Message, state: FSMContext):
    """
    Обработчик команды /change_city.
    Переводит пользователя на шаг выбора города.
    """
    await state.set_state(OrderProcess.SelectCity)
    await message.answer("""Вы хотите изменить город. 
                         Пожайлуста, Выберете город, в котором вы находитесь:""", reply_markup=city_selection_keyboard())
