# Приветствие и регистрация пользователей
import logging

from aiogram.types import Message
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from ..keyboards import create_main_menu_keyboard, create_catalog_keyboard, create_city_selection_keyboard
from ..states import OrderProcess

# Настройка логирования
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Константы
AVAILABLE_CITIES = ["Вроцлав", "Краков", "Варшава", "Познань"]

REGISTER_PROMPT = "Привет! Пожалуйста, зарегистрируйтесь. Как вас зовут?"

WELCOME_BACK_MSG = "С возвращением, {user_name} из города {user_city}! Чем могу помочь?"

SELECT_CITY_PROMPT = "Спасибо! Теперь выберете город, в котором Вы находитесь:"

NAME_INVALID_MSG = ("Введенное вами имя слишком короткое или содержит недопустимые символы,"
                    " введите корректное имя.")

CITY_INVALID_MSG = ("Этого города нет в списке."
                    "Выберите город из предложенного списка")

WELCOME_NEW_USER_MSG = ("Рад с Вами познакомиться {user_name} из {user_city}!"
                        " Перейдите в каталог, что бы ознакомится с товарами магазина")

CHANGE_CITY_PROMPT = ("Вы хотите изменить город?"
                      " Пожалуйста выберите город в котором Вы находитесь:")
# Создаем маршрутизатор
router = Router()

def is_valid_name(name: str) -> bool:
    """Проверяет корректность имени пользователя"""
    return len(name) >= 2 and all(part.isalpha() for part in name.split("-"))

def format_city(city: str) -> str:
    """Формирует название города"""
    return city.strip().title()

@router.message(Command('start'))
async def cmd_start(message: Message, state: FSMContext):
    """
    Обработчик команды /start.
    Приветствует пользователя и запускает процесс регистрации.
    """
    logger.info(f"Получена команда /start от пользователя {message.from_user.id}.")
    try:
        # Проверяем, зарегистрирован ли пользователь
        user_data = await state.get_data()
        logger.debug(f"Текущее данные пользователя {message.from_user.id}: {user_data}")

        if user_data and {"name", "city"} <= user_data.keys():
            await message.answer(
                WELCOME_BACK_MSG.format(user_name=user_data["name"],
                                        user_city=user_data["city"]),
                reply_markup=create_main_menu_keyboard()
            )
            logger.info(
                f"Пользователь {message.from_user.id} успешно авторизован."
                f"Имя пользователя: {user_data['name']}, Город: {user_data['city']}."
            )
        else:
            await state.set_state(OrderProcess.Registration)
            logger.info(f"Пользователь начал регистрацию {message.from_user.id}.")
            await message.answer(REGISTER_PROMPT, reply_markup=create_main_menu_keyboard())
    except Exception as e:
        logger.error(f"Произошла ошибка при обработке /start для пользователя"
                     f"{message.from_user.id}: {str(e)}.")
        await message.answer(f"Произошла ошибка: {str(e)}."
                             f" Пожалуйста, попробуйте снова.")

@router.message(OrderProcess.Registration)
async def user_registration(message: Message, state: FSMContext):
    """ 
    Обрабатывает ввод имени пользователя.
    Сохраняет имя в состоянии и переводит пользователя на следующий шаг.
    """
    user_name = message.text.strip()
    logger.info(f"Пользователь {message.from_user.id} вводит имя: {user_name}")
    if not is_valid_name(user_name):
        logger.warning(f"Некорректное имя от пользователя {message.from_user.id}: {user_name}. ")
        await message.answer(NAME_INVALID_MSG)
        return
    await state.update_data(name=user_name)
    logger.info(f"Имя {user_name} сохранено для пользователя {message.from_user.id}:")
    await state.set_state(OrderProcess.SelectCity)
    await message.answer(SELECT_CITY_PROMPT,
                         reply_markup=create_city_selection_keyboard())


@router.message(OrderProcess.SelectCity)
async def user_select_city(message: Message, state: FSMContext):
    """
    Обрабатывает выбор города пользователем.
    Сохраняет город в состоянии и завершает процесс регистрации.
    """
    user_city = format_city(message.text)
    logger.info(f"Пользователь {message.from_user.id} выберает город: {user_city}.")
    if user_city not in AVAILABLE_CITIES:
        logger.warning(f"Некорректный город от пользователя {message.from_user.id}: {user_city}.")
        await message.answer(CITY_INVALID_MSG)
        return
    await state.update_data(city=user_city)
    user_data = await state.get_data()
    logger.info(f"Город {user_city} сохранен для пользователя {message.from_user.id}:")
    await message.answer(
        WELCOME_NEW_USER_MSG.format(user_name=user_data["name"],
                                    user_city=user_city),
        reply_markup=create_catalog_keyboard(categories=[])
    )


@router.message(Command('change_city'))
async def cmd_change_city(message: Message, state: FSMContext):
    """Обработчик команды /change_city."""
    logger.info(f"Пользователь {message.from_user.id} инициировал изменение города")
    await state.set_state(OrderProcess.SelectCity)
    await message.answer(CHANGE_CITY_PROMPT, reply_markup=create_city_selection_keyboard())