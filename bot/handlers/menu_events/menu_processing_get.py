from sqlalchemy.ext.asyncio import AsyncSession

from handlers.menu_events.menu_main import main_menu, checkout
from handlers.menu_events.menu_process_cart import carts
from handlers.menu_events.menu_process_catalog import catalog, products


# Функция для обработки запросов меню на основе уровня и действия
async def get_menu_content(
        session: AsyncSession,
        level: int,
        menu_name: str,
        product_id: int | None = None,
        category: int | None = None,
        page: int | None = None,
        user_id: int | None = None,
):
    # Проверяем уровень меню и вызываем соответствующую функцию
    if level == 0:  # Главная страница
        return await main_menu(session, level, menu_name)
    elif level == 1:  # Каталог
        return await catalog(session, level, menu_name)
    elif level == 2:  # Товары в каталоге
        return await products(session, level, category, page)
    elif level == 3:  # Корзина
        return await carts(session, level, menu_name, page, user_id, product_id)
    elif level == 4:  # Новый уровень для завершения покупки
        return await checkout(session,  user_id)