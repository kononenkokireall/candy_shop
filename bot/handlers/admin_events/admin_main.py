import logging

from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter, or_f
from aiogram.fsm.context import FSMContext

from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Order
from database.orm_querys.orm_query_banner import (
    orm_get_info_pages,
    orm_change_banner_image,

)
from database.orm_querys.orm_query_category import orm_get_categories
from database.orm_querys.orm_query_order import get_order_by_id
from database.orm_querys.orm_query_product import (
    orm_get_product,
    orm_get_products,
    orm_update_product,
    orm_add_product,
    orm_delete_product
)

from filters.chat_types import ChatTypeFilter, IsAdmin

from keyboards.inline_main import get_callback_btn
from keyboards.linline_admin import OrderAction

from keyboards.reply import get_keyboard

from states.states import OrderProcess, AddBanner

# Создаем роутер для работы с администраторами
admin_router = Router()
# Устанавливаем фильтр для работы только в личных сообщениях и только для администраторов
admin_router.message.filter(ChatTypeFilter(["private"]), IsAdmin())

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Клавиатура для администратора (главное меню)
ADMIN_KB = get_keyboard(
    "Добавить товар",
    "Ассортимент",
    "Добавить/Изменить баннер",
    placeholder="Выберите действие",
    sizes=(2,),
)

###############################Точка входа в события администратора####################################################

# Handler команды /admin для входа в функционал администратора
@admin_router.message(Command("admin"))
async def admin_features(message: types.Message):
    await message.answer("Что хотите сделать?", reply_markup=ADMIN_KB)


#####################################Команды для администратора########################################################

# Handler команды (отмена) и сброса состояния
@admin_router.message(StateFilter("*"), Command("отмена"))
@admin_router.message(StateFilter("*"), F.text.casefold() == "отмена")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()  # Получаем текущее состояние машины состояний
    if current_state is None: # Если состояния нет, завершаем выполнение
        return
    if OrderProcess.product_for_change: # Сбрасываем объект изменения, если он существует
        OrderProcess.product_for_change = None
    await state.clear() # Сбрасываем все состояния FSM
    # Возвращаем пользователя в главное меню
    await message.answer("Действия отменены", reply_markup=ADMIN_KB)


# Handler для команды(возврата на шаг назад в FSM)
@admin_router.message(StateFilter("*"), Command("назад"))
@admin_router.message(StateFilter("*"), F.text.casefold() == "назад")
async def back_step_handler(message: types.Message, state: FSMContext) -> None:
    # Получаем текущее состояние FSM
    current_state = await state.get_state()

    # Проверяем, если пользователь уже на самом первом шаге
    if current_state == OrderProcess.NAME:
        await message.answer(
            'Предыдущего шага нет, или введите название товара или напишите "отмена"'
        )
        return

    previous = None
    # Перебираем все состояния FSM, чтобы установить предыдущее состояние
    for step in OrderProcess.__all_states__:
        if step.state == current_state:
            # Устанавливаем предыдущее состояние
            await state.set_state(previous)
            await message.answer(
                f"Ок, вы вернулись к прошлому шагу \n"
                f"{OrderProcess.TEXTS[previous.state]}"
                # Выводим текст для прошлого шага
            )
            return
        previous = step


###################################FSM_states для администратора#######################################################

# Становимся в состояние ожидания ввода name
@admin_router.message(StateFilter(None), F.text == "Добавить товар")
async def add_product(message: types.Message, state: FSMContext):
    await message.answer(
        "Введите название товара",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(OrderProcess.NAME)


# Handler для отображения ассортимента (категорий товаров)
@admin_router.message(F.text == 'Ассортимент')
async def admin_features(message: types.Message, session: AsyncSession):
    # Получаем категории из базы данных
    categories = await orm_get_categories(session)
    # Генерируем кнопки с категориями
    btn = {category.name : f'category_{category.id}' for category in categories}
    await message.answer("Выберите категорию",
                         reply_markup=get_callback_btn(btn=btn))


# Handler для отправки перечня информационных страниц и входа в состояние загрузки изображения
@admin_router.message(StateFilter(None), F.text == 'Добавить/Изменить баннер')
async def add_image2(message: types.Message, state: FSMContext, session: AsyncSession):
    # Получаем список страниц
    pages_names = [page.name for page in await orm_get_info_pages(session)]
    await message.answer(f"Отправьте фото баннера.\n"
                         f"В описании укажите для какой страницы:\n"
                         f"{', '.join(pages_names)}")
    # Устанавливаем состояние-загрузку изображения
    await state.set_state(AddBanner.IMAGE)



##############################Handler Изменение названия товара для администратора#####################################

# Handler для изменения названия товара (вход в состояние name)
@admin_router.callback_query(StateFilter(None), F.data.startswith("change_"))
async def change_product_callback(
        callback: types.CallbackQuery,
        state: FSMContext,
        session: AsyncSession
):
    product_id = callback.data.split("_")[-1]

    product_for_change = await orm_get_product(session, int(product_id))
    # Получаем товар для изменения
    OrderProcess.product_for_change = product_for_change
    # Просим администратора ввести название товара
    await callback.answer()
    await callback.message.answer(
        "Введите название товара",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(OrderProcess.NAME)


# Handler для введения изменения названия товара.
# Получаем данные для состояния name и потом меняем состояние на DESCRIPTION
@admin_router.message(OrderProcess.NAME, F.text)
async def add_name(message: types.Message, state: FSMContext):
    # Проверяем, если пользователь хочет оставить старое название
    if message.text == "." and OrderProcess.product_for_change:
        await state.update_data(name=OrderProcess.product_for_change.name)
        # Обновляем данные FSM
    else:
        # Здесь можно сделать какую либо дополнительную проверку
        # и выйти из handler не меняя состояние с отправкой соответствующего сообщения
        # например:
        # Проверка длины введенного названия
        if 4 >= len(message.text) >= 150:
            await message.answer(
                "Название товара не должно превышать 150 символов\n"
                "или быть менее 5 ти символов. \n"
                "Введите заново"
            )
            return

        # Обновляем данные FSM
        await state.update_data(name=message.text)
    # Переходим к следующему шагу
    await message.answer("Введите описание товара")
    await state.set_state(OrderProcess.DESCRIPTION)

# Handler для некорректного ввода на шаге NAME
@admin_router.message(OrderProcess.NAME)
async def add_name2(message: types.Message):
    await message.answer("Вы ввели не допустимые данные, введите текст названия товара")


##############################Handler Изменение описания товара для администратора#####################################

# Handler для получения описания товара
@admin_router.message(OrderProcess.DESCRIPTION, F.text)
async def add_description(message: types.Message, state: FSMContext, session: AsyncSession):
    # Проверяем, если пользователь хочет оставить старое описание
    if message.text == "." and OrderProcess.product_for_change:
        await state.update_data(description=OrderProcess.product_for_change.description)
    else:
        # Проверка минимальной длины описания
        if 4 >= len(message.text):
            await message.answer(
                "Слишком короткое описание. \n"
                "Введите заново"
            )
            return
        await state.update_data(description=message.text)  # Обновляем данные FSM

    # Генерация кнопок с категориями
    categories = await orm_get_categories(session)
    btn = {category.name: str(category.id) for category in categories}
    # Переход к выбору категории
    await message.answer("Выберите категорию",
                         reply_markup=get_callback_btn(btn=btn))
    await state.set_state(OrderProcess.CATEGORY)


# Handler для некорректного ввода на шаге DESCRIPTION
@admin_router.message(OrderProcess.DESCRIPTION)
async def add_description2(message: types.Message):
    await message.answer("Вы ввели не допустимые данные, введите текст описания товара")


##############################Handler выбора категории товара для администратора#######################################

# Handler для отображения товаров из выбранной категории
@admin_router.callback_query(F.data.startswith('category_'))
async def starring_at_product(callback: types.CallbackQuery, session: AsyncSession):
    category_id = callback.data.split('_')[-1]# Получаем ID категории
    # Перебираем все товары из базы данных для данной категории
    for product in await orm_get_products(session, int(category_id)):
        await callback.message.answer_photo(
            product.image,
            caption=f"<strong>{product.name}\
                    </strong>\n{product.description}\n"
                    f"Стоимость: {round(product.price, 2)}",
            reply_markup=get_callback_btn(
                btn={
                    "Удалить": f"delete_{product.id}",
                    "Изменить": f"change_{product.id}",
                },
                sizes=(2,)
            ),
        )
    await callback.answer()
    await callback.message.answer("ОК, вот список товаров ⏫")


# Handler для выбора категории через Callback
@admin_router.callback_query(OrderProcess.CATEGORY)
async def category_choice(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    if int(callback.data) in [category.id for category in
                              await orm_get_categories(session)]:  # Проверяем валидность выбранной категории
        await callback.answer()  # Подтверждаем выбор
        await state.update_data(category=callback.data)  # Сохраняем выбранную категорию в данные FSM
        await callback.message.answer('Теперь введите цену товара.')  # Переходим к следующему шагу
        await state.set_state(OrderProcess.PRICE)
    else:
        await callback.message.answer('Выберите категорию из кнопок.')  # Сообщение об ошибке
        await callback.answer()


# Handler для некорректного ввода на шаге CATEGORY
@admin_router.message(OrderProcess.CATEGORY)
async def category_choice2(message: types.Message):
    await message.answer("'Выберите категорию из кнопок.'")


##############################Handler Изменение цены товара для администратора########################################

# Handler для изменения цены товара
@admin_router.message(OrderProcess.PRICE, F.text)
async def add_price(message: types.Message, state: FSMContext):
    if message.text == "." and OrderProcess.product_for_change:  # Проверяем, если пользователь хочет оставить старую цену
        await state.update_data(price=OrderProcess.product_for_change.price)
    else:
        try:
            float(message.text)  # Проверяем, что введенная цена является числом
        except ValueError:
            await message.answer("Введите корректное значение цены")
            return

        await state.update_data(price=message.text)  # Обновляем данные FSM
    await message.answer("Загрузите изображение товара")  # Переход к загрузке изображения
    await state.set_state(OrderProcess.ADD_IMAGES)


# Handler для некорректного ввода на шаге PRICE
@admin_router.message(OrderProcess.PRICE)
async def add_price2(message: types.Message):
    await message.answer("Вы ввели не допустимые данные, введите стоимость товара")


##########################Handler Изменение/Добавление баннера меню для администратора#################################

# Добавляем/изменяем изображение в таблице (там уже есть записанные страницы по именам:
# main, catalog, cart(для пустой корзины), about, payment, shipping
@admin_router.message(AddBanner.IMAGE, F.photo)
async def add_banner(message: types.Message, state: FSMContext, session: AsyncSession):
    image_id = message.photo[-1].file_id
    for_page = message.caption.strip()
    pages_names = [page.name for page in await orm_get_info_pages(session)]
    if for_page not in pages_names:
        await message.answer(f"Введите нормальное название страницы, например:\
                         \n{', '.join(pages_names)}")
        return
    await orm_change_banner_image(session, for_page, image_id,)
    await message.answer("Баннер добавлен/изменен.")
    await state.clear()

# Получение некорректного ввода
@admin_router.message(AddBanner.IMAGE)
async def add_banner2(message: types.Message):
    await message.answer("Отправьте фото баннера или отмена")


##############################Handler Изменение фото товара для администратора#########################################

# Handler для добавления/изменения изображения товара
@admin_router.message(OrderProcess.ADD_IMAGES, or_f(F.photo, F.casefold()))
async def add_image(message: types.Message, state: FSMContext, session: AsyncSession):
    # Проверяем, если пользователь хочет оставить старое изображение
    if message.text and message.text == "." and OrderProcess.product_for_change:
        await state.update_data(image=OrderProcess.product_for_change.image)

    elif message.photo:  # Проверяем, что пользователь отправил фото
        await state.update_data(image=message.photo[-1].file_id)
    else:
        await message.answer("Отправьте фото пищи")  # Сообщение об ошибке
        return

    data = await state.get_data()  # Получаем все данные FSM
    try:
        if OrderProcess.product_for_change:  # Проверяем, если происходит изменение существующего товара
            await orm_update_product(session, OrderProcess.product_for_change.id, data)  # Обновляем товар
        else:
            await orm_add_product(session, data)  # Добавляем товар
        await message.answer("Товар добавлен/Изменен", reply_markup=ADMIN_KB)  # Сообщение об успехе
        await state.clear()  # Сбрасываем состояние FSM

    except Exception as e:  # Обработка ошибок
        await message.answer(
            f"Ошибка: \n{str(e)}\n"
            f"Обратись к разработчику",
            reply_markup=ADMIN_KB,
        )
        await state.clear()

    OrderProcess.product_for_change = None  # Сброс объекта изменения


# Handler для некорректного действия на шаге ADD_IMAGES
@admin_router.message(OrderProcess.ADD_IMAGES)
async def add_image2(message: types.Message):
    await message.answer("Отправьте фото пищи")


##############################Handler удаления товара для администратора##############################################

# Handler для удаления товара
@admin_router.callback_query(F.data.startswith("delete_"))
async def delete_product_callback(callback: types.CallbackQuery, session: AsyncSession):
    product_id = callback.data.split("_")[-1] # Получаем ID продукта для удаления
    await orm_delete_product(session, int(product_id)) # Удаляем товар из базы данных

    await callback.answer("Товар удален")
    await callback.message.answer("Товар удален!")


##############################Handler подтверждения оплаты товара для администратора###################################

# Обработчик для подтверждения заказа (кнопка "✅ Подтвердить заказ")
# 2. Обработчик с правильным использованием фильтров
@admin_router.callback_query(
    OrderAction.filter(F.callback_data.action == "confirm")
)
async def confirm_order_handler(
        callback: types.CallbackQuery,
        callback_data: OrderAction,
        session: AsyncSession
):
    try:
        # 3. Получение данных из callback_data
        order_id = callback_data.order_id

        # 4. Получение заказа с блокировкой для избежания race condition
        async with session.begin():
            order = await session.get(
                Order,
                order_id,
                with_for_update=True  # Блокировка записи
            )

            if not order:
                await callback.answer("🚨 Заказ не найден", show_alert=True)
                return

            if order.status == "confirmed":
                await callback.answer("ℹ️ Заказ уже подтвержден")
                return

            # 5. Обновление статуса
            order.status = "confirmed"
            await session.commit()

            # 6. Отправка уведомления пользователю
            try:
                await callback.bot.send_message(
                    chat_id=order.user_id,
                    text=(
                        "🎉 <b>Ваш заказ подтвержден!</b>\n\n"
                        "✅ Оплата прошла успешно\n"
                        "📦 Забрать можно по адресу: ул. Примерная, 123"
                    ),
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления: {e}")

            await callback.answer("✅ Заказ подтвержден")

    except Exception as e:
        logger.error(f"Ошибка подтверждения: {e}", exc_info=True)
        await session.rollback()
        await callback.answer("🚨 Ошибка подтверждения заказа", show_alert=True)


# Обработчик для отмены заказа (кнопка "❌ Отменить заказ")
@admin_router.callback_query(
    OrderAction.filter(F.callback_data.action == "cancel")
)
async def cancel_order_handler(
        callback: types.CallbackQuery,
        callback_data: OrderAction,
        session: AsyncSession
):
    try:
        # Используем контекстный менеджер для транзакции
        async with session.begin():
            # Получаем заказ с блокировкой записи
            order = await session.get(
                Order,
                callback_data.order_id,
                with_for_update=True  # Блокировка для конкурентного доступа
            )

            if not order:
                await callback.answer("🚨 Заказ не найден", show_alert=True)
                return

            if order.status == "cancelled":
                await callback.answer("ℹ️ Заказ уже отменен")
                return

            # Обновляем статус
            order.status = "cancelled"

            # Коммит транзакции
            await session.commit()

            # Отправка уведомления
            try:
                await callback.bot.send_message(
                    chat_id=order.user_id,
                    text=(
                        "❌ <b>Заказ отменен</b>\n\n"
                        "Администратор отменил ваш заказ. "
                        "Для уточнения деталей свяжитесь с поддержкой."
                    ),
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления: {e}")
                raise

            await callback.answer("✅ Заказ отменен")

    except Exception as e:
        logger.error(f"Ошибка отмены: {e}", exc_info=True)
        await session.rollback()
        await callback.answer("🚨 Ошибка отмены заказа", show_alert=True)
