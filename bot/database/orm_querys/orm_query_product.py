############ Зона администратора: добавить/изменить/удалить товар ########################
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Product


# Добавление нового товара
async def orm_add_product(session: AsyncSession, data: dict):
    """
    Добавляет новый товар в базу данных. Информация о товаре передается через словарь `data`.
    """
    obj = Product(
        name=data["name"],
        description=data["description"],
        price=float(data["price"]),
        image=data["image"],
        category_id=int(data["category"]),
    )
    session.add(obj)
    await session.commit()


# Получение всех товаров определенной категории
async def orm_get_products(session: AsyncSession, category_id):
    """
    Возвращает список товаров в указанной категории.
    """
    query = select(Product).where(Product.category_id == int(category_id))
    result = await session.execute(query)
    return result.scalars().all()


# Получение информации о конкретном товаре
async def orm_get_product(session: AsyncSession, product_id: int):
    """
    Возвращает информацию о товаре по его ID.
    """
    query = select(Product).where(Product.id == product_id)
    result = await session.execute(query)
    return result.scalar()


# Обновление информации о товаре
async def orm_update_product(session: AsyncSession, product_id: int, data):
    """
    Обновляет информацию о товаре с заданным ID, используя данные из словаря `data`.
    """
    query = (
        update(Product)
        .where(Product.id == product_id)
        .values(
            name=data["name"],
            description=data["description"],
            price=float(data["price"]),
            image=data["image"],
            category_id=int(data["category"]),
        )
    )
    await session.execute(query)
    await session.commit()


# Удаление товара
async def orm_delete_product(session: AsyncSession, product_id: int):
    """
    Удаляет товар из базы данных по его ID.
    """
    query = delete(Product).where(Product.id == product_id)
    await session.execute(query)
    await session.commit()