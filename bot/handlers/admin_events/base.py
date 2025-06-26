import logging

from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_querys.orm_query_banner import orm_get_info_pages
from database.orm_querys.orm_query_category import orm_get_categories
from filters.chat_types import ChatTypeFilter, IsAdmin
from handlers.admin_events.admin_main import admin_router_root
from keyboards.inline_main import get_callback_btn
from keyboards.reply import get_keyboard
from states.states import OrderProcess, AddBanner

# логгер
logger = logging.getLogger("admin")

menu_keyboard_router = Router(name="admin_menu")
admin_router_root.message.filter(ChatTypeFilter(["private"]), IsAdmin())

# Клавиатура для администратора (главное меню)
ADMIN_KB = get_keyboard(
    "Добавить товар",
    "Ассортимент",
    "Добавить/Изменить баннер",
    placeholder="Выберите действие",
    sizes=(2,),
)


# Handler команды /admin для входа в функционал администратора
@admin_router_root.message(Command("admin"))
async def admin_question(
        message: types.Message
) -> None:
    await message.answer("Что хотите сделать?", reply_markup=ADMIN_KB)


# Handler команды (отмена) и сброса состояния
@admin_router_root.message(StateFilter("*"), Command("отмена"))
@admin_router_root.message(StateFilter("*"), F.text.casefold() == "отмена")
async def cancel_handler(
        message: types.Message,
        state: FSMContext
) -> None:
    current_state = await state.get_state()
    # Получаем текущее состояние машины состояний
    if current_state is None:
        # Если состояния нет, завершаем выполнение
        return
    if OrderProcess.product_for_change:
        # Сбрасываем объект изменения, если он существует
        OrderProcess.product_for_change = None
    await state.clear()
    # Сбрасываем все состояния FSM
    # Возвращаем пользователя в главное меню
    await message.answer("Действия отменены", reply_markup=ADMIN_KB)


# Handler для команды(возврата на шаг назад в FSM)
@admin_router_root.message(StateFilter("*"), Command("назад"))
@admin_router_root.message(StateFilter("*"), F.text.casefold() == "назад")
async def back_step_handler(
        message: types.Message,
        state: FSMContext
) -> None:
    # Получаем текущее состояние FSM
    current_state = await state.get_state()

    # Проверка наличия состояния
    if current_state is None:
        await message.answer("❌ Нет активного состояния")
        return

    if current_state == OrderProcess.NAME:
        await message.answer('⚠️ Вы уже на первом шаге')
        return

    previous = None
    # Перебираем все состояния FSM, чтобы установить предыдущее состояние
    for step in OrderProcess.__all_states__:
        if step.state == current_state:
            if previous is None:
                await message.answer("🚨 Невозможно вернуться назад")
                return
            # Устанавливаем предыдущее состояние
            await state.set_state(previous)
            await message.answer(
                f"Ок, вы вернулись к прошлому шагу \n"
                f"{OrderProcess.TEXTS[previous.state]}"
                # Выводим текст для прошлого шага
            )
            return
        previous = step


# Handler Становимся в состояние ожидания ввода name
@admin_router_root.message(F.text == "Добавить товар")
async def add_product(
        message: types.Message,
        state: FSMContext
) -> None:
    await state.clear()
    OrderProcess.product_for_change = None

    await message.answer(
        "Введите название товара",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(OrderProcess.NAME)


# Handler для отображения ассортимента (категорий товаров)
@admin_router_root.message(F.text == 'Ассортимент')
async def admin_features(
        message: types.Message,
        state: FSMContext,
        session: AsyncSession
) -> None:
    await state.clear()
    OrderProcess.product_for_change = None
    # Получаем категории из базы данных
    categories = await orm_get_categories(session)
    # Генерируем кнопки с категориями (исправлено обращение к атрибутам)
    btn = {
        category.name: f'category_{category.id}'
        for category in categories
        if category.name is not None  # Проверка на наличие названия
    }

    await message.answer(
        "Выберите категорию",
        reply_markup=get_callback_btn(btn=btn)
    )


# Handler для отправки перечня информационных
# страниц и входа в состояние загрузки изображения
@admin_router_root.message(StateFilter(None),
                           F.text == 'Добавить/Изменить баннер')
async def add_and_change_image(
        message: types.Message,
        state: FSMContext,
        session: AsyncSession
) -> None:
    await state.clear()
    OrderProcess.product_for_change = None
    # Получаем список страниц
    pages_names = [page.name for page in await orm_get_info_pages(session)]
    await message.answer(f"Отправьте фото баннера.\n"
                         f"В описании укажите для какой страницы:\n"
                         f"{', '.join(pages_names)}")
    # Устанавливаем состояние-загрузку изображения
    await state.set_state(AddBanner.IMAGE)
